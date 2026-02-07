from django.utils import timezone
from django.db import models
from apps.patients.models import Patient


class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    scheduled_at = models.DateTimeField(null=False, default=timezone.now)
    duration_minutes = models.IntegerField(default=15, null=False)
    reason = models.CharField(max_length=400, blank=True, null=True)
    status = models.CharField(
        max_length=15,
        choices=[
            ("PL", "PLANNED"),
            ("CI", "CHECKED_IN"),
            ("CN", "CANCELLED"),
        ],
        default="PL",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.full_name} at {self.scheduled_at:%Y-%m-%d %H:%M}"
