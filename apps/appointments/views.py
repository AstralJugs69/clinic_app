from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from .models import Appointment
from .forms import AppointmentForm
from apps.accounts.utils import log_action


@login_required
def appointment_today(request):
    """Display today's schedule with optional patient name search."""
    today = timezone.localdate()
    q = request.GET.get("q", "").strip()

    # Filter by today first, then apply search filter
    appointments = (
        Appointment.objects.filter(scheduled_at__date=today)
        .select_related("patient")
        .order_by("scheduled_at")
    )

    if q:
        appointments = appointments.filter(patient__full_name__icontains=q)

    return render(
        request, "appointments/today.html", {"appointments": appointments, "q": q}
    )


@login_required
def appointment_new(request):
    """Create a new appointment with PRG pattern."""
    initial = {}
    if request.GET.get("patient"):
        initial["patient"] = request.GET.get("patient")

    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save()
            log_action(
                request,
                action="created_appointment",
                target_type="appointment",
                target_id=appointment.id,
                description=(
                    f"Created appointment: {appointment.patient.full_name} at "
                    f"{timezone.localtime(appointment.scheduled_at).strftime('%Y-%m-%d %H:%M')}"
                ),
            )
            return redirect("appointments:today")
    else:
        form = AppointmentForm(initial=initial)

    return render(request, "appointments/appointment_form.html", {"form": form})


@login_required
def api_today_appointments(request):
    today = timezone.localdate()
    appointments = (
        Appointment.objects.filter(scheduled_at__date=today)
        .select_related("patient")
        .order_by("scheduled_at")
    )
    payload = [
        {
            "id": item.id,
            "patient_id": item.patient_id,
            "patient_name": item.patient.full_name,
            "scheduled_at": timezone.localtime(item.scheduled_at).isoformat(),
            "duration_minutes": item.duration_minutes,
            "reason": item.reason,
            "status": item.status,
        }
        for item in appointments
    ]
    return JsonResponse(payload, safe=False)
