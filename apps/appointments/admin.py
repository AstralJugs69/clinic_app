from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "scheduled_at",
        "duration_minutes",
        "reason",
        "status",
        "created_at",
    )
    search_fields = ("patient__full_name", "status", "reason")
