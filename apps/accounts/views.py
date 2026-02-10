from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
from .models import ActionLog, UserProfile
from .utils import log_action
from .permissions import role_home_url, role_required

User = get_user_model()


class StaffLoginView(LoginView):
    template_name = "registration/login.html"

    def get_success_url(self):
        next_url = self.get_redirect_url()
        if next_url:
            return next_url
        return role_home_url(self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(
            self.request,
            action="login",
            target_type="user",
            target_id=self.request.user.id,
            description=f"User logged in: {self.request.user.username}",
        )
        return response


@login_required
def logout_view(request):
    username = request.user.username
    user_id = request.user.id
    log_action(
        request,
        action="logout",
        target_type="user",
        target_id=user_id,
        description=f"User logged out: {username}",
    )
    auth_logout(request)
    return redirect("login")


def home_redirect(request):
    if not request.user.is_authenticated:
        return redirect("login")
    return redirect(role_home_url(request.user))


@login_required
@role_required("admin")
def activity(request):
    """Display activity logs with filtering and pagination."""
    logs = ActionLog.objects.select_related("user")

    # Filter by action type
    action_filter = request.GET.get("action", "")
    if action_filter:
        logs = logs.filter(action=action_filter)

    # Filter by date range
    date_filter = request.GET.get("date", "")
    if date_filter == "today":
        logs = logs.filter(created_at__date=timezone.localdate())
    elif date_filter == "week":
        week_ago = timezone.now() - timedelta(days=7)
        logs = logs.filter(created_at__gte=week_ago)
    elif date_filter == "month":
        month_ago = timezone.now() - timedelta(days=30)
        logs = logs.filter(created_at__gte=month_ago)

    # Search by description or username
    search = request.GET.get("q", "").strip()
    if search:
        logs = logs.filter(
            Q(description__icontains=search) | Q(user__username__icontains=search)
        )

    # TODO: Add pagination later
    # For now, limit to 50 most recent logs
    logs = logs[:50]

    # Get action choices for filter dropdown
    action_choices = ActionLog.ACTION_CHOICES

    # Activity stats for the header
    today = timezone.localdate()
    stats = {
        "today_count": ActionLog.objects.filter(created_at__date=today).count(),
        "week_count": ActionLog.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count(),
        "total_count": ActionLog.objects.count(),
    }

    return render(
        request,
        "accounts/activity.html",
        {
            "logs": logs,
            "action_choices": action_choices,
            "current_action": action_filter,
            "current_date": date_filter,
            "search": search,
            "stats": stats,
        },
    )


@login_required
@role_required("admin")
def api_logs(request):
    logs = ActionLog.objects.select_related("user")[:50]
    payload = [
        {
            "id": log.id,
            "user": log.user.username if log.user else None,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "description": log.description,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
    return JsonResponse(payload, safe=False)


@login_required
def profile(request):
    """View and edit current user's profile."""
    # Get or create profile
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        # Update user fields
        request.user.first_name = request.POST.get("first_name", "")
        request.user.last_name = request.POST.get("last_name", "")
        request.user.email = request.POST.get("email", "")
        request.user.save()

        # Update profile fields
        profile_obj.phone = request.POST.get("phone", "")
        profile_obj.department = request.POST.get("department", "")
        profile_obj.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("accounts:profile")

    return render(request, "accounts/profile.html", {"profile": profile_obj})


@login_required
@role_required("admin")
def staff_list(request):
    """View list of staff members (admin only)."""
    profiles = UserProfile.objects.select_related("user").filter(is_active_staff=True)

    # Filter by role
    role_filter = request.GET.get("role", "")
    if role_filter:
        profiles = profiles.filter(role=role_filter)

    return render(
        request,
        "accounts/staff_list.html",
        {
            "profiles": profiles,
            "role_choices": UserProfile.ROLE_CHOICES,
            "current_role": role_filter,
        },
    )
