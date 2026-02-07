from .models import ActionLog


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_action(request_or_user, action, target_type="", target_id=None, description=""):
    """
    Create an ActionLog entry.
    
    Args:
        request_or_user: Either an HttpRequest object or a User object
        action: String code e.g. "created_patient", "created_appointment"
        target_type: String e.g. "patient", "appointment" (optional)
        target_id: Integer ID of the target object (optional)
        description: Human-readable description of the action (optional)
    
    Returns:
        The created ActionLog instance
    """
    # Handle both request and user being passed
    if hasattr(request_or_user, 'user'):
        # It's a request object
        user = request_or_user.user if request_or_user.user.is_authenticated else None
        ip_address = get_client_ip(request_or_user)
    else:
        # It's a user object
        user = request_or_user if request_or_user and hasattr(request_or_user, 'is_authenticated') and request_or_user.is_authenticated else None
        ip_address = None
    
    return ActionLog.objects.create(
        user=user,
        action=action,
        target_type=target_type,
        target_id=target_id,
        description=description,
        ip_address=ip_address
    )


def log_patient_action(request, action, patient, description=""):
    """Convenience function for patient-related actions."""
    if not description:
        description = f"{action.replace('_', ' ').title()}: {patient.full_name}"
    return log_action(request, action, "patient", patient.id, description)


def log_appointment_action(request, action, appointment, description=""):
    """Convenience function for appointment-related actions."""
    if not description:
        description = f"{action.replace('_', ' ').title()}: {appointment.patient.full_name} at {appointment.scheduled_at.strftime('%H:%M')}"
    return log_action(request, action, "appointment", appointment.id, description)
