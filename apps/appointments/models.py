from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.patients.models import Patient


class CareRoom(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Appointment(models.Model):
    STATUS_PLANNED = "PL"
    STATUS_WAITING_DOCTOR = "WD"
    STATUS_WITH_DOCTOR = "MD"
    STATUS_WAITING_ROOM = "WR"
    STATUS_WITH_ROOM = "MR"
    STATUS_COMPLETED = "CM"
    STATUS_CANCELLED = "CN"

    STATUS_CHOICES = [
        (STATUS_PLANNED, "Planned"),
        (STATUS_WAITING_DOCTOR, "Waiting for doctor"),
        (STATUS_WITH_DOCTOR, "With doctor"),
        (STATUS_WAITING_ROOM, "Waiting for room"),
        (STATUS_WITH_ROOM, "In room"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    scheduled_at = models.DateTimeField(default=timezone.now)
    duration_minutes = models.IntegerField(default=15)
    reason = models.CharField(max_length=400, blank=True, null=True)
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default=STATUS_PLANNED
    )
    assigned_room = models.ForeignKey(
        CareRoom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["scheduled_at", "id"]

    def __str__(self):
        return f"{self.patient.full_name} at {self.scheduled_at:%Y-%m-%d %H:%M}"


class AppointmentEvent(models.Model):
    EVENT_CHECKED_IN = "checked_in"
    EVENT_DOCTOR_ACCEPTED = "doctor_accepted"
    EVENT_TRANSFERRED_TO_ROOM = "transferred_to_room"
    EVENT_ROOM_ACCEPTED = "room_accepted"
    EVENT_ROOM_TRANSFERRED = "room_transferred"
    EVENT_COMPLETED = "completed_appointment"

    EVENT_CHOICES = [
        (EVENT_CHECKED_IN, "Checked in"),
        (EVENT_DOCTOR_ACCEPTED, "Doctor accepted"),
        (EVENT_TRANSFERRED_TO_ROOM, "Transferred to room"),
        (EVENT_ROOM_ACCEPTED, "Room accepted"),
        (EVENT_ROOM_TRANSFERRED, "Transferred to another room"),
        (EVENT_COMPLETED, "Completed"),
    ]

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES)
    from_status = models.CharField(max_length=15, blank=True)
    to_status = models.CharField(max_length=15)
    room = models.ForeignKey(
        CareRoom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointment_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.event_type} #{self.appointment_id}"
