from django.contrib import admin
from .models import ActionLog, UserProfile


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "user", "action", "target_type", "target_id", "description", "ip_address"]
    list_filter = ["action", "target_type", "created_at"]
    search_fields = ["description", "user__username", "ip_address"]
    readonly_fields = ["user", "action", "target_type", "target_id", "description", "ip_address", "created_at"]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"
    
    def has_add_permission(self, request):
        return False  # Logs are created programmatically only
    
    def has_change_permission(self, request, obj=None):
        return False  # Logs should not be edited


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "phone", "department", "is_active_staff", "created_at"]
    list_filter = ["role", "is_active_staff", "department"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "phone"]
    ordering = ["user__username"]
    raw_id_fields = ["user"]
    
    fieldsets = (
        (None, {
            "fields": ("user", "role", "is_active_staff")
        }),
        ("Contact", {
            "fields": ("phone", "department")
        }),
        ("Display", {
            "fields": ("avatar_initials",),
            "classes": ("collapse",)
        }),
    )
