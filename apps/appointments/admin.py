from django.contrib import admin
from .models import Appointment, CareRoom, AppointmentEvent


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "scheduled_at",
        "duration_minutes",
        "reason",
        "status",
        "assigned_room",
        "created_at",
    )
    list_filter = ("status", "assigned_room")
    search_fields = ("patient__full_name", "status", "reason", "assigned_room__name")


@admin.register(CareRoom)
class CareRoomAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    ordering = ("sort_order", "name")


@admin.register(AppointmentEvent)
class AppointmentEventAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "appointment",
        "event_type",
        "from_status",
        "to_status",
        "room",
        "performed_by",
    )
    list_filter = ("event_type", "to_status", "room")
    search_fields = ("appointment__patient__full_name", "performed_by__username")
    readonly_fields = (
        "appointment",
        "event_type",
        "from_status",
        "to_status",
        "room",
        "performed_by",
        "created_at",
    )

    def has_add_permission(self, request):
        return False
