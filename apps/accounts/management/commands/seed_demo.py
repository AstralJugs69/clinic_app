from datetime import datetime, time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.utils import log_action
from apps.appointments.models import Appointment
from apps.patients.models import Patient


class Command(BaseCommand):
    help = "Seed demo user, patients, and appointments for ClinicFlow Lite"

    def handle(self, *args, **options):
        User = get_user_model()

        demo_user, created = User.objects.get_or_create(
            username="demo_staff",
            defaults={"is_staff": True},
        )
        if created:
            demo_user.set_password("DemoPass123!")
            demo_user.save()
            self.stdout.write(
                self.style.SUCCESS("Created demo user: demo_staff / DemoPass123!")
            )
        else:
            self.stdout.write("Demo user already exists: demo_staff")

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
                    demo_user,
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

        first_patient = Patient.objects.order_by("id").first()
        if first_patient:
            today = timezone.localdate()
            scheduled_at = timezone.make_aware(
                datetime.combine(today, time(hour=9, minute=0))
            )
            appt, appt_created = Appointment.objects.get_or_create(
                patient=first_patient,
                scheduled_at=scheduled_at,
                reason="Demo follow-up",
                defaults={"duration_minutes": 20, "status": "PL"},
            )
            if appt_created:
                log_action(
                    demo_user,
                    action="created_appointment",
                    target_type="appointment",
                    target_id=appt.id,
                    description=f"Seeded appointment: {first_patient.full_name}",
                )
                self.stdout.write(self.style.SUCCESS("Created demo appointment"))
            else:
                self.stdout.write("Demo appointment already exists")

        self.stdout.write(
            self.style.WARNING(
                "Demo credentials -> username: demo_staff, password: DemoPass123!"
            )
        )
