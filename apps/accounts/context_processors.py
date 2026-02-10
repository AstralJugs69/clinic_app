from .permissions import get_user_role, role_home_url


def role_navigation(request):
    if not request.user.is_authenticated:
        return {
            "user_role": "",
            "role_home_url": "",
            "nav_rooms": [],
        }

    role = get_user_role(request.user)
    nav_rooms = []

    if role in {"admin", "nurse"}:
        from apps.appointments.models import CareRoom

        nav_rooms = list(
            CareRoom.objects.filter(is_active=True).order_by("sort_order", "name")[:5]
        )

    return {
        "user_role": role,
        "role_home_url": role_home_url(request.user),
        "nav_rooms": nav_rooms,
    }
