from datetime import datetime, time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.accounts.utils import log_action
from apps.appointments.models import Appointment, CareRoom
from apps.patients.models import Patient


class Command(BaseCommand):
    help = "Seed demo user, patients, and appointments for ClinicFlow Lite"

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

    def handle(self, *args, **options):
        User = get_user_model()

        receptionist_user = self._ensure_staff_user(
            User,
            "demo_staff",
            "DemoPass123!",
            "receptionist",
        )
        self._ensure_staff_user(User, "demo_doctor", "DemoPass123!", "doctor")
        self._ensure_staff_user(User, "demo_nurse", "DemoPass123!", "nurse")

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

        patients = [
            {
                "full_name": "Selam Tesfaye",
                "phone": "+251912345678",
                "sex": "F",
                "mrn": "MRN-1001",
                "address": "Bole, Addis Ababa",
            },
            {
                "full_name": "Abebe Kebede",
                "phone": "+251911223344",
                "sex": "M",
                "mrn": "MRN-1002",
                "address": "Arat Kilo, Addis Ababa",
            },
        ]

        created_patients = []
        for payload in patients:
            patient, patient_created = Patient.objects.get_or_create(
                full_name=payload["full_name"],
                defaults=payload,
            )
            if patient_created:
                log_action(
                    receptionist_user,
                    action="created_patient",
                    target_type="patient",
                    target_id=patient.id,
                    description=f"Seeded patient: {patient.full_name}",
                )
                created_patients.append(patient)

        if created_patients:
            self.stdout.write(
                self.style.SUCCESS(f"Created {len(created_patients)} patients")
            )
        else:
            self.stdout.write("Patients already seeded")

        today = timezone.localdate()
        patient_list = list(Patient.objects.order_by("id")[:2])
        schedule_times = [time(hour=9, minute=0), time(hour=9, minute=20)]

        for index, patient in enumerate(patient_list):
            scheduled_at = timezone.make_aware(
                datetime.combine(today, schedule_times[index])
            )
            appt, appt_created = Appointment.objects.get_or_create(
                patient=patient,
                scheduled_at=scheduled_at,
                defaults={
                    "duration_minutes": 20,
                    "reason": "Demo follow-up",
                    "status": Appointment.STATUS_PLANNED,
                },
            )
            if appt_created:
                log_action(
                    receptionist_user,
                    action="created_appointment",
                    target_type="appointment",
                    target_id=appt.id,
                    description=f"Seeded appointment: {patient.full_name}",
                )

        self.stdout.write(self.style.SUCCESS("Demo rooms and appointments are ready"))

        self.stdout.write(
            self.style.WARNING(
                "Demo credentials -> demo_staff / demo_doctor / demo_nurse | password: DemoPass123!"
            )
        )
