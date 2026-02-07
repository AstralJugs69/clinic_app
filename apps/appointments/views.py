from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import AppointmentForm
from .models import Appointment, CareRoom
from .realtime import broadcast_workflow_event
from .workflow import transition_appointment
from apps.accounts.utils import log_action


def _today_queryset():
    today = timezone.localdate()
    return (
        Appointment.objects.filter(scheduled_at__date=today)
        .select_related("patient", "assigned_room")
        .order_by("scheduled_at", "id")
    )


def _rooms_queryset():
    return CareRoom.objects.filter(is_active=True).order_by("sort_order", "name")


def _validation_error_text(error):
    if hasattr(error, "messages"):
        return " ".join(error.messages)
    return str(error)


@login_required
def appointment_today(request):
    """Display today's schedule with optional patient name search."""
    q = request.GET.get("q", "").strip()

    appointments = _today_queryset()

    if q:
        appointments = appointments.filter(patient__full_name__icontains=q)

    return render(
        request,
        "appointments/today.html",
        {
            "appointments": appointments,
            "q": q,
            "rooms": _rooms_queryset(),
        },
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
            appointment.status = Appointment.STATUS_PLANNED
            appointment.assigned_room = None
            appointment.save(update_fields=["status", "assigned_room"])

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
            broadcast_workflow_event(
                appointment=appointment,
                action="created_appointment",
                actor=request.user.username,
            )
            return redirect("appointments:today")
    else:
        form = AppointmentForm(initial=initial)

    return render(request, "appointments/appointment_form.html", {"form": form})


@login_required
def frontdesk_feed(request):
    appointments = _today_queryset().exclude(
        status__in=[Appointment.STATUS_COMPLETED, Appointment.STATUS_CANCELLED]
    )
    return render(
        request,
        "appointments/frontdesk_feed.html",
        {
            "appointments": appointments,
            "rooms": _rooms_queryset(),
        },
    )


@login_required
def doctor_feed(request):
    base = _today_queryset()
    waiting_doctor = base.filter(status=Appointment.STATUS_WAITING_DOCTOR)
    with_doctor = base.filter(status=Appointment.STATUS_WITH_DOCTOR)
    return render(
        request,
        "appointments/doctor_feed.html",
        {
            "waiting_doctor": waiting_doctor,
            "with_doctor": with_doctor,
            "rooms": _rooms_queryset(),
        },
    )


@login_required
def room_feed(request, room_code):
    room = get_object_or_404(CareRoom, code=room_code, is_active=True)
    base = _today_queryset()
    waiting_room = base.filter(
        status=Appointment.STATUS_WAITING_ROOM,
        assigned_room=room,
    )
    in_room = base.filter(
        status=Appointment.STATUS_WITH_ROOM,
        assigned_room=room,
    )
    return render(
        request,
        "appointments/room_feed.html",
        {
            "room": room,
            "waiting_room": waiting_room,
            "in_room": in_room,
            "rooms": _rooms_queryset(),
            "other_rooms": _rooms_queryset().exclude(pk=room.pk),
        },
    )


def _transition_and_redirect(request, pk, action, fallback_url_name):
    next_url = request.POST.get("next") or reverse(fallback_url_name)
    room_id = request.POST.get("room_id") or None

    try:
        appointment, _event = transition_appointment(
            appointment_id=pk,
            action=action,
            user=request.user,
            room_id=room_id,
        )
        messages.success(
            request,
            f"{appointment.patient.full_name} -> {appointment.get_status_display()}",
        )
    except PermissionDenied as exc:
        messages.error(request, str(exc))
    except ValidationError as exc:
        messages.error(request, _validation_error_text(exc))
    except Appointment.DoesNotExist:
        messages.error(request, "Appointment not found.")

    return redirect(next_url)


@login_required
@require_POST
def appointment_check_in(request, pk):
    return _transition_and_redirect(
        request, pk, "check_in", "appointments:frontdesk_feed"
    )


@login_required
@require_POST
def appointment_doctor_accept(request, pk):
    return _transition_and_redirect(
        request,
        pk,
        "doctor_accept",
        "appointments:doctor_feed",
    )


@login_required
@require_POST
def appointment_transfer_to_room(request, pk):
    return _transition_and_redirect(
        request,
        pk,
        "transfer_to_room",
        "appointments:doctor_feed",
    )


@login_required
@require_POST
def appointment_room_accept(request, pk):
    return _transition_and_redirect(
        request,
        pk,
        "room_accept",
        "appointments:frontdesk_feed",
    )


@login_required
@require_POST
def appointment_room_transfer(request, pk):
    return _transition_and_redirect(
        request,
        pk,
        "room_transfer",
        "appointments:frontdesk_feed",
    )


@login_required
@require_POST
def appointment_complete(request, pk):
    return _transition_and_redirect(
        request, pk, "complete", "appointments:frontdesk_feed"
    )


@login_required
def api_today_appointments(request):
    appointments = _today_queryset()

    payload = [
        {
            "id": item.id,
            "patient_id": item.patient_id,
            "patient_name": item.patient.full_name,
            "scheduled_at": timezone.localtime(item.scheduled_at).isoformat(),
            "duration_minutes": item.duration_minutes,
            "reason": item.reason,
            "status": item.status,
            "status_label": item.get_status_display(),
            "room": item.assigned_room.code if item.assigned_room else None,
            "room_name": item.assigned_room.name if item.assigned_room else None,
        }
        for item in appointments
    ]
    return JsonResponse(payload, safe=False)
