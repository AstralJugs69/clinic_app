from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.patients.models import Patient

from .models import Appointment, AppointmentEvent, CareRoom
from .workflow import transition_appointment


class WorkflowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.receptionist = User.objects.create_user("reception", password="pass1234")
        self.doctor = User.objects.create_user("doctor", password="pass1234")
        self.nurse = User.objects.create_user("nurse", password="pass1234")

        UserProfile.objects.create(user=self.receptionist, role="receptionist")
        UserProfile.objects.create(user=self.doctor, role="doctor")
        UserProfile.objects.create(user=self.nurse, role="nurse")

        self.patient = Patient.objects.create(
            full_name="Test Patient",
            phone="+251911111111",
            sex="M",
        )
        self.room_lab = CareRoom.objects.create(code="LAB", name="Lab", sort_order=1)
        self.room_pharm = CareRoom.objects.create(
            code="PHARM", name="Pharmacy", sort_order=2
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            scheduled_at=timezone.now() + timedelta(hours=1),
            duration_minutes=15,
            status=Appointment.STATUS_PLANNED,
        )

    def test_receptionist_can_check_in(self):
        updated, event = transition_appointment(
            appointment_id=self.appointment.id,
            action="check_in",
            user=self.receptionist,
        )

        self.assertEqual(updated.status, Appointment.STATUS_WAITING_DOCTOR)
        self.assertEqual(event.event_type, AppointmentEvent.EVENT_CHECKED_IN)

    def test_receptionist_cannot_doctor_accept(self):
        transition_appointment(
            appointment_id=self.appointment.id,
            action="check_in",
            user=self.receptionist,
        )

        with self.assertRaises(PermissionDenied):
            transition_appointment(
                appointment_id=self.appointment.id,
                action="doctor_accept",
                user=self.receptionist,
            )

    def test_only_one_patient_can_be_with_doctor(self):
        second_patient = Patient.objects.create(
            full_name="Second Patient",
            phone="+251933444555",
            sex="F",
        )
        second_appointment = Appointment.objects.create(
            patient=second_patient,
            scheduled_at=timezone.now() + timedelta(hours=2),
            duration_minutes=15,
            status=Appointment.STATUS_PLANNED,
        )

        transition_appointment(
            appointment_id=self.appointment.id,
            action="check_in",
            user=self.receptionist,
        )
        transition_appointment(
            appointment_id=self.appointment.id,
            action="doctor_accept",
            user=self.doctor,
        )

        with self.assertRaises(ValidationError):
            transition_appointment(
                appointment_id=second_appointment.id,
                action="check_in",
                user=self.receptionist,
            )

        second_appointment.refresh_from_db()
        self.assertEqual(second_appointment.status, Appointment.STATUS_PLANNED)

    def test_cannot_accept_second_waiting_patient_while_busy(self):
        second_patient = Patient.objects.create(
            full_name="Third Patient",
            phone="+251944555666",
            sex="M",
        )
        second_appointment = Appointment.objects.create(
            patient=second_patient,
            scheduled_at=timezone.now() + timedelta(hours=2),
            duration_minutes=15,
            status=Appointment.STATUS_WAITING_DOCTOR,
        )

        transition_appointment(
            appointment_id=self.appointment.id,
            action="check_in",
            user=self.receptionist,
        )
        transition_appointment(
            appointment_id=self.appointment.id,
            action="doctor_accept",
            user=self.doctor,
        )

        with self.assertRaises(ValidationError):
            transition_appointment(
                appointment_id=second_appointment.id,
                action="doctor_accept",
                user=self.doctor,
            )

        second_appointment.refresh_from_db()
        self.assertEqual(second_appointment.status, Appointment.STATUS_WAITING_DOCTOR)

    def test_full_doctor_and_room_flow(self):
        transition_appointment(
            appointment_id=self.appointment.id,
            action="check_in",
            user=self.receptionist,
        )
        transition_appointment(
            appointment_id=self.appointment.id,
            action="doctor_accept",
            user=self.doctor,
        )
        transition_appointment(
            appointment_id=self.appointment.id,
            action="transfer_to_room",
            user=self.doctor,
            room_id=self.room_lab.id,
        )
        transition_appointment(
            appointment_id=self.appointment.id,
            action="room_accept",
            user=self.nurse,
        )
        updated, _event = transition_appointment(
            appointment_id=self.appointment.id,
            action="complete",
            user=self.nurse,
        )

        self.assertEqual(updated.status, Appointment.STATUS_COMPLETED)

    def test_room_transfer_must_change_destination(self):
        transition_appointment(
            appointment_id=self.appointment.id,
            action="check_in",
            user=self.receptionist,
        )
        transition_appointment(
            appointment_id=self.appointment.id,
            action="doctor_accept",
            user=self.doctor,
        )
        transition_appointment(
            appointment_id=self.appointment.id,
            action="transfer_to_room",
            user=self.doctor,
            room_id=self.room_lab.id,
        )
        transition_appointment(
            appointment_id=self.appointment.id,
            action="room_accept",
            user=self.nurse,
        )

        with self.assertRaises(ValidationError):
            transition_appointment(
                appointment_id=self.appointment.id,
                action="room_transfer",
                user=self.nurse,
                room_id=self.room_lab.id,
            )

        updated, _event = transition_appointment(
            appointment_id=self.appointment.id,
            action="room_transfer",
            user=self.nurse,
            room_id=self.room_pharm.id,
        )
        self.assertEqual(updated.status, Appointment.STATUS_WAITING_ROOM)
        self.assertEqual(updated.assigned_room_id, self.room_pharm.id)


class FrontdeskIntakeTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.receptionist = User.objects.create_user("reception", password="pass1234")
        UserProfile.objects.create(user=self.receptionist, role="receptionist")
        self.patient = Patient.objects.create(
            full_name="Walk In",
            phone="+251922333444",
            sex="F",
        )

    def test_frontdesk_intake_creates_checked_in_appointment(self):
        self.client.force_login(self.receptionist)

        response = self.client.post(
            reverse("appointments:frontdesk_intake"),
            {
                "patient": self.patient.id,
                "reason": "Headache",
                "duration_minutes": 20,
            },
        )

        self.assertEqual(response.status_code, 302)
        appointment = Appointment.objects.get(patient=self.patient)
        self.assertEqual(appointment.status, Appointment.STATUS_WAITING_DOCTOR)
        self.assertEqual(appointment.reason, "Headache")

    def test_frontdesk_intake_emergency_tags_reason(self):
        self.client.force_login(self.receptionist)

        self.client.post(
            reverse("appointments:frontdesk_intake"),
            {
                "patient": self.patient.id,
                "reason": "Chest pain",
                "duration_minutes": 20,
                "emergency": "on",
            },
        )

        appointment = Appointment.objects.get(patient=self.patient)
        self.assertTrue(appointment.reason.startswith("[EMERGENCY]"))
