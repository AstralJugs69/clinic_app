import random
from datetime import date, datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.accounts.utils import log_action
from apps.appointments.models import Appointment, CareRoom
from apps.appointments import workflow as appointment_workflow
from apps.appointments.workflow import transition_appointment
from apps.patients.models import Patient


FIRST_NAMES_MALE = [
    "Abebe",
    "Bekele",
    "Dawit",
    "Elias",
    "Fikru",
    "Girma",
    "Henok",
    "Kebede",
    "Luel",
    "Mekonnen",
    "Nahom",
    "Robel",
    "Sami",
    "Tadesse",
    "Yonas",
]

FIRST_NAMES_FEMALE = [
    "Aster",
    "Bethlehem",
    "Chaltu",
    "Dagmawit",
    "Eden",
    "Feven",
    "Genet",
    "Helen",
    "Kidist",
    "Lulit",
    "Mahi",
    "Rahel",
    "Saron",
    "Selam",
    "Tsion",
]

LAST_NAMES = [
    "Abate",
    "Alemu",
    "Assefa",
    "Bekele",
    "Demissie",
    "Fikre",
    "Gebremariam",
    "Kassa",
    "Kebede",
    "Mamo",
    "Mesfin",
    "Solomon",
    "Tadesse",
    "Tesfaye",
    "Wolde",
]

ADDRESSES = [
    "Bole, Addis Ababa",
    "Kirkos, Addis Ababa",
    "Yeka, Addis Ababa",
    "Arat Kilo, Addis Ababa",
    "Piassa, Addis Ababa",
    "CMC, Addis Ababa",
    "Kolfe, Addis Ababa",
    "Megenagna, Addis Ababa",
    "Lebu, Addis Ababa",
    "Sarbet, Addis Ababa",
]

REASONS = [
    "General consultation",
    "Follow-up visit",
    "Headache and fatigue",
    "Blood pressure check",
    "Diabetes follow-up",
    "Lab test review",
    "Prescription refill",
    "Abdominal pain",
    "Persistent cough",
    "Skin rash",
    "Back pain",
    "Annual checkup",
]

EMERGENCY_REASONS = [
    "Severe chest pain",
    "Shortness of breath",
    "Fainting episode",
    "High fever with confusion",
    "Severe bleeding",
]

TODAY_STATUS_WEIGHTS = [
    (Appointment.STATUS_PLANNED, 18),
    (Appointment.STATUS_WAITING_DOCTOR, 24),
    (Appointment.STATUS_WITH_DOCTOR, 14),
    (Appointment.STATUS_WAITING_ROOM, 14),
    (Appointment.STATUS_WITH_ROOM, 10),
    (Appointment.STATUS_COMPLETED, 14),
    (Appointment.STATUS_CANCELLED, 6),
]

FUTURE_STATUS_WEIGHTS = [
    (Appointment.STATUS_PLANNED, 75),
    (Appointment.STATUS_WAITING_DOCTOR, 10),
    (Appointment.STATUS_WITH_DOCTOR, 8),
    (Appointment.STATUS_CANCELLED, 7),
]

PAST_STATUS_WEIGHTS = [
    (Appointment.STATUS_COMPLETED, 65),
    (Appointment.STATUS_WITH_ROOM, 10),
    (Appointment.STATUS_WAITING_ROOM, 8),
    (Appointment.STATUS_WITH_DOCTOR, 7),
    (Appointment.STATUS_WAITING_DOCTOR, 5),
    (Appointment.STATUS_CANCELLED, 5),
]


class Command(BaseCommand):
    help = "Seed demo users, patients, and appointments for ClinicFlow Lite"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Clear existing data before seeding",
        )
        parser.add_argument(
            "--patients",
            type=int,
            default=150,
            help="How many patients to generate",
        )
        parser.add_argument(
            "--appointments",
            type=int,
            default=420,
            help="How many appointments to generate",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=2026,
            help="Random seed for deterministic data",
        )

    def _ensure_staff_user(self, User, username, password, role):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"is_staff": True},
        )
        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
            self.stdout.write(
                self.style.SUCCESS(f"Created demo user: {username} / {password}")
            )
        elif not user.is_staff:
            user.is_staff = True
            user.save(update_fields=["is_staff"])

        profile, _ = UserProfile.objects.get_or_create(user=user)
        if profile.role != role:
            profile.role = role
            profile.save(update_fields=["role"])

        return user

    def _weighted_pick(self, rng, weighted_values):
        total = sum(weight for _value, weight in weighted_values)
        pick = rng.uniform(0, total)
        cursor = 0
        for value, weight in weighted_values:
            cursor += weight
            if pick <= cursor:
                return value
        return weighted_values[-1][0]

    def _random_phone(self, rng):
        return f"+2519{rng.randint(10000000, 99999999)}"

    def _random_dob(self, rng):
        year = rng.randint(1952, 2012)
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        return date(year, month, day)

    def _build_name(self, rng, sex, index):
        first_names = FIRST_NAMES_FEMALE if sex == "F" else FIRST_NAMES_MALE
        first = rng.choice(first_names)
        last = rng.choice(LAST_NAMES)
        return f"{first} {last} {index:03d}"

    def _make_scheduled_at(self, rng):
        bucket_roll = rng.random()
        if bucket_roll < 0.5:
            day_offset = 0
            status_weights = TODAY_STATUS_WEIGHTS
        elif bucket_roll < 0.75:
            day_offset = rng.randint(1, 6)
            status_weights = FUTURE_STATUS_WEIGHTS
        else:
            day_offset = -rng.randint(1, 4)
            status_weights = PAST_STATUS_WEIGHTS

        target_date = timezone.localdate() + timedelta(days=day_offset)
        hour = rng.randint(8, 16)
        minute = rng.choice([0, 10, 20, 30, 40, 50])
        scheduled_at = timezone.make_aware(
            datetime.combine(target_date, time(hour, minute))
        )
        status = self._weighted_pick(rng, status_weights)
        return scheduled_at, status, day_offset

    def _apply_status_flow(
        self,
        *,
        appointment,
        target_status,
        receptionist,
        doctors,
        nurses,
        rooms,
        rng,
    ):
        if target_status == Appointment.STATUS_CANCELLED:
            appointment.status = Appointment.STATUS_CANCELLED
            appointment.save(update_fields=["status"])
            log_action(
                receptionist,
                action="cancelled_appointment",
                target_type="appointment",
                target_id=appointment.id,
                description=f"Cancelled appointment for patient: {appointment.patient.full_name}",
            )
            return

        if target_status in {
            Appointment.STATUS_WAITING_DOCTOR,
            Appointment.STATUS_WITH_DOCTOR,
            Appointment.STATUS_WAITING_ROOM,
            Appointment.STATUS_WITH_ROOM,
            Appointment.STATUS_COMPLETED,
        }:
            appointment, _event = transition_appointment(
                appointment_id=appointment.id,
                action="check_in",
                user=receptionist,
            )

        if target_status in {
            Appointment.STATUS_WITH_DOCTOR,
            Appointment.STATUS_WAITING_ROOM,
            Appointment.STATUS_WITH_ROOM,
            Appointment.STATUS_COMPLETED,
        }:
            doctor = rng.choice(doctors)
            appointment, _event = transition_appointment(
                appointment_id=appointment.id,
                action="doctor_accept",
                user=doctor,
            )

        if target_status in {
            Appointment.STATUS_WAITING_ROOM,
            Appointment.STATUS_WITH_ROOM,
            Appointment.STATUS_COMPLETED,
        }:
            doctor = rng.choice(doctors)
            destination_room = rng.choice(rooms)
            appointment, _event = transition_appointment(
                appointment_id=appointment.id,
                action="transfer_to_room",
                user=doctor,
                room_id=destination_room.id,
            )

        if target_status in {
            Appointment.STATUS_WITH_ROOM,
            Appointment.STATUS_COMPLETED,
        }:
            nurse = rng.choice(nurses)
            appointment, _event = transition_appointment(
                appointment_id=appointment.id,
                action="room_accept",
                user=nurse,
            )

        if target_status == Appointment.STATUS_COMPLETED:
            nurse = rng.choice(nurses)
            if len(rooms) > 1 and rng.random() < 0.2:
                available_rooms = [
                    r for r in rooms if r.id != appointment.assigned_room_id
                ]
                if available_rooms:
                    transfer_room = rng.choice(available_rooms)
                    appointment, _event = transition_appointment(
                        appointment_id=appointment.id,
                        action="room_transfer",
                        user=nurse,
                        room_id=transfer_room.id,
                    )
                    appointment, _event = transition_appointment(
                        appointment_id=appointment.id,
                        action="room_accept",
                        user=nurse,
                    )

            appointment, _event = transition_appointment(
                appointment_id=appointment.id,
                action="complete",
                user=nurse,
            )

    def _seed_patients(self, *, count, rng, receptionist_user):
        patients = []
        for index in range(1, count + 1):
            sex = rng.choice(["M", "F"])
            patient = Patient.objects.create(
                full_name=self._build_name(rng, sex, index),
                phone=self._random_phone(rng),
                sex=sex,
                date_of_birth=self._random_dob(rng),
                mrn=f"MRN-{3000 + index}",
                address=rng.choice(ADDRESSES),
            )
            patients.append(patient)
            log_action(
                receptionist_user,
                action="created_patient",
                target_type="patient",
                target_id=patient.id,
                description=f"Seeded patient: {patient.full_name}",
            )

        self.stdout.write(self.style.SUCCESS(f"Created {len(patients)} patients"))
        return patients

    def _seed_appointments(
        self,
        *,
        count,
        rng,
        patients,
        rooms,
        receptionist_user,
        doctors,
        nurses,
    ):
        status_counter = {status: 0 for status, _label in Appointment.STATUS_CHOICES}
        for _index in range(count):
            patient = rng.choice(patients)
            scheduled_at, target_status, day_offset = self._make_scheduled_at(rng)

            is_emergency = day_offset == 0 and rng.random() < 0.12
            if is_emergency:
                reason = f"[EMERGENCY] {rng.choice(EMERGENCY_REASONS)}"
            else:
                reason = rng.choice(REASONS)

            appointment = Appointment.objects.create(
                patient=patient,
                scheduled_at=scheduled_at,
                duration_minutes=rng.choice([10, 15, 20, 25, 30, 40]),
                reason=reason,
                status=Appointment.STATUS_PLANNED,
            )

            log_action(
                receptionist_user,
                action="created_appointment",
                target_type="appointment",
                target_id=appointment.id,
                description=(
                    f"Seeded appointment: {patient.full_name} at "
                    f"{timezone.localtime(appointment.scheduled_at).strftime('%Y-%m-%d %H:%M')}"
                ),
            )

            self._apply_status_flow(
                appointment=appointment,
                target_status=target_status,
                receptionist=receptionist_user,
                doctors=doctors,
                nurses=nurses,
                rooms=rooms,
                rng=rng,
            )

            appointment.refresh_from_db(fields=["status"])
            status_counter[appointment.status] = (
                status_counter.get(appointment.status, 0) + 1
            )

        summary = ", ".join(
            f"{code}:{count}" for code, count in sorted(status_counter.items()) if count
        )
        self.stdout.write(
            self.style.SUCCESS(f"Created {count} appointments ({summary})")
        )

    def handle(self, *args, **options):
        rng = random.Random(options["seed"])

        if options["reset"]:
            call_command("flush", interactive=False, verbosity=0)
            self.stdout.write(self.style.WARNING("Database cleared."))

        User = get_user_model()

        receptionist_user = self._ensure_staff_user(
            User,
            "demo_staff",
            "DemoPass123!",
            "receptionist",
        )
        doctors = [
            self._ensure_staff_user(User, "demo_doctor", "DemoPass123!", "doctor"),
            self._ensure_staff_user(User, "demo_doctor2", "DemoPass123!", "doctor"),
        ]
        nurses = [
            self._ensure_staff_user(User, "demo_nurse", "DemoPass123!", "nurse"),
            self._ensure_staff_user(User, "demo_nurse2", "DemoPass123!", "nurse"),
        ]

        room_specs = [
            {"code": "CONS2", "name": "Consultation-2", "sort_order": 1},
            {"code": "LAB", "name": "Lab", "sort_order": 2},
            {"code": "PHARM", "name": "Pharmacy", "sort_order": 3},
        ]
        for room_spec in room_specs:
            CareRoom.objects.update_or_create(
                code=room_spec["code"],
                defaults={
                    "name": room_spec["name"],
                    "sort_order": room_spec["sort_order"],
                    "is_active": True,
                },
            )
        rooms = list(
            CareRoom.objects.filter(is_active=True).order_by("sort_order", "name")
        )

        patients = self._seed_patients(
            count=max(1, options["patients"]),
            rng=rng,
            receptionist_user=receptionist_user,
        )
        original_broadcast = appointment_workflow.broadcast_workflow_event
        appointment_workflow.broadcast_workflow_event = lambda *args, **kwargs: None
        try:
            self._seed_appointments(
                count=max(1, options["appointments"]),
                rng=rng,
                patients=patients,
                rooms=rooms,
                receptionist_user=receptionist_user,
                doctors=doctors,
                nurses=nurses,
            )
        finally:
            appointment_workflow.broadcast_workflow_event = original_broadcast

        self.stdout.write(self.style.SUCCESS("Comprehensive demo data is ready."))

        self.stdout.write(
            self.style.WARNING(
                "Demo credentials -> demo_staff / demo_doctor / demo_doctor2 / "
                "demo_nurse / demo_nurse2 | password: DemoPass123!"
            )
        )
