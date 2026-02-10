from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

from .models import UserProfile


def get_user_role(user):
    if not user or not user.is_authenticated:
        return ""
    if user.is_superuser:
        return "admin"

    try:
        return user.profile.role
    except UserProfile.DoesNotExist:
        if user.is_staff:
            return "receptionist"
        return ""


def role_home_url(user):
    role = get_user_role(user)

    if role in {"admin", "receptionist"}:
        return reverse("appointments:frontdesk_feed")
    if role == "doctor":
        return reverse("appointments:doctor_feed")
    if role == "nurse":
        from apps.appointments.models import CareRoom

        room = (
            CareRoom.objects.filter(is_active=True)
            .order_by("sort_order", "name")
            .first()
        )
        if room:
            return reverse("appointments:room_feed", kwargs={"room_code": room.code})
        return reverse("accounts:profile")

    if user and user.is_authenticated:
        return reverse("accounts:profile")
    return reverse("login")


def role_required(*allowed_roles):
    allowed = set(allowed_roles)

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            role = get_user_role(request.user)
            if role == "admin" or role in allowed:
                return view_func(request, *args, **kwargs)

            if request.user.is_authenticated:
                messages.error(request, "You do not have access to that page.")
                return redirect(role_home_url(request.user))
            return redirect("login")

        return _wrapped

    return decorator
