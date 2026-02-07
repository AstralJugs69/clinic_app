from django.db import models
from django.contrib.auth.models import User


class ActionLog(models.Model):
    """Log of user actions for audit trail."""
    
    ACTION_CHOICES = [
        ("created_patient", "Created Patient"),
        ("updated_patient", "Updated Patient"),
        ("created_appointment", "Created Appointment"),
        ("updated_appointment", "Updated Appointment"),
        ("cancelled_appointment", "Cancelled Appointment"),
        ("checked_in", "Checked In Patient"),
        ("login", "User Login"),
        ("logout", "User Logout"),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="action_logs"
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target_type = models.CharField(max_length=50, blank=True)  # "patient", "appointment"
    target_id = models.IntegerField(null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)  # Human-readable description
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"
    
    def __str__(self):
        return f"{self.get_action_display()} by {self.user or 'Anonymous'}"
    
    @property
    def action_icon(self):
        """Return an icon/emoji for the action type."""
        icons = {
            "created_patient": "👤",
            "updated_patient": "✏️",
            "created_appointment": "📅",
            "updated_appointment": "📝",
            "cancelled_appointment": "❌",
            "checked_in": "✅",
            "login": "🔐",
            "logout": "🚪",
        }
        return icons.get(self.action, "📋")
    
    @property
    def action_color(self):
        """Return CSS color class for the action type."""
        colors = {
            "created_patient": "green",
            "updated_patient": "blue",
            "created_appointment": "indigo",
            "updated_appointment": "blue",
            "cancelled_appointment": "red",
            "checked_in": "emerald",
            "login": "purple",
            "logout": "gray",
        }
        return colors.get(self.action, "gray")


class UserProfile(models.Model):
    """Extended user profile for staff members."""
    
    ROLE_CHOICES = [
        ("admin", "Administrator"),
        ("doctor", "Doctor"),
        ("nurse", "Nurse"),
        ("receptionist", "Receptionist"),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="receptionist")
    phone = models.CharField(max_length=30, blank=True)
    department = models.CharField(max_length=100, blank=True)
    avatar_initials = models.CharField(max_length=2, blank=True)  # For avatar display
    is_active_staff = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
        # Auto-generate initials from username or full name
        if not self.avatar_initials:
            name = self.user.get_full_name() or self.user.username
            parts = name.split()
            if len(parts) >= 2:
                self.avatar_initials = (parts[0][0] + parts[-1][0]).upper()
            else:
                self.avatar_initials = name[:2].upper()
        super().save(*args, **kwargs)
