from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.appointments.models import CareRoom


class RoleAccessTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.receptionist = User.objects.create_user("reception", password="pass1234")
        self.doctor = User.objects.create_user("doctor", password="pass1234")
        self.nurse = User.objects.create_user("nurse", password="pass1234")
        self.admin = User.objects.create_superuser(
            "admin",
            email="admin@example.com",
            password="pass1234",
        )

        UserProfile.objects.create(user=self.receptionist, role="receptionist")
        UserProfile.objects.create(user=self.doctor, role="doctor")
        UserProfile.objects.create(user=self.nurse, role="nurse")

        self.room = CareRoom.objects.create(code="CONS2", name="Consultation-2")

    def test_receptionist_login_redirects_to_frontdesk(self):
        response = self.client.post(
            reverse("login"),
            {"username": "reception", "password": "pass1234"},
        )
        self.assertRedirects(response, reverse("appointments:frontdesk_feed"))

    def test_doctor_login_redirects_to_doctor_feed(self):
        response = self.client.post(
            reverse("login"),
            {"username": "doctor", "password": "pass1234"},
        )
        self.assertRedirects(response, reverse("appointments:doctor_feed"))

    def test_nurse_login_redirects_to_room_feed(self):
        response = self.client.post(
            reverse("login"),
            {"username": "nurse", "password": "pass1234"},
        )
        self.assertRedirects(
            response,
            reverse("appointments:room_feed", kwargs={"room_code": self.room.code}),
        )

    def test_doctor_cannot_access_patients_list(self):
        self.client.force_login(self.doctor)
        response = self.client.get(reverse("patients:list"), follow=True)

        self.assertRedirects(response, reverse("appointments:doctor_feed"))

    def test_receptionist_cannot_access_doctor_feed(self):
        self.client.force_login(self.receptionist)
        response = self.client.get(reverse("appointments:doctor_feed"), follow=True)

        self.assertRedirects(response, reverse("appointments:frontdesk_feed"))

    def test_nurse_cannot_access_frontdesk_feed(self):
        self.client.force_login(self.nurse)
        response = self.client.get(reverse("appointments:frontdesk_feed"), follow=True)

        self.assertRedirects(
            response,
            reverse("appointments:room_feed", kwargs={"room_code": self.room.code}),
        )

    def test_admin_can_access_all_major_pages(self):
        self.client.force_login(self.admin)

        pages = [
            reverse("patients:list"),
            reverse("appointments:frontdesk_feed"),
            reverse("appointments:doctor_feed"),
            reverse("appointments:room_feed", kwargs={"room_code": self.room.code}),
            reverse("activity"),
        ]

        for page in pages:
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(response.status_code, 200)

    def test_root_redirects_to_role_home(self):
        self.client.force_login(self.nurse)
        response = self.client.get(reverse("home"))
        self.assertRedirects(
            response,
            reverse("appointments:room_feed", kwargs={"room_code": self.room.code}),
        )
