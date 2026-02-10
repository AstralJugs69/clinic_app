from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.accounts.utils import log_action

from .models import Appointment, AppointmentEvent, CareRoom
from .realtime import broadcast_workflow_event


ACTION_RULES = {
    "check_in": {
        "from": {Appointment.STATUS_PLANNED},
        "to": Appointment.STATUS_WAITING_DOCTOR,
        "roles": {"receptionist", "admin"},
        "requires_room": False,
    },
    "doctor_accept": {
        "from": {Appointment.STATUS_WAITING_DOCTOR},
        "to": Appointment.STATUS_WITH_DOCTOR,
        "roles": {"doctor", "admin"},
        "requires_room": False,
    },
    "transfer_to_room": {
        "from": {Appointment.STATUS_WITH_DOCTOR},
        "to": Appointment.STATUS_WAITING_ROOM,
        "roles": {"doctor", "admin"},
        "requires_room": True,
    },
    "room_accept": {
        "from": {Appointment.STATUS_WAITING_ROOM},
        "to": Appointment.STATUS_WITH_ROOM,
        "roles": {"nurse", "admin"},
        "requires_room": False,
    },
    "room_transfer": {
        "from": {Appointment.STATUS_WITH_ROOM},
        "to": Appointment.STATUS_WAITING_ROOM,
        "roles": {"nurse", "admin"},
        "requires_room": True,
    },
    "complete": {
        "from": {Appointment.STATUS_WITH_ROOM},
        "to": Appointment.STATUS_COMPLETED,
        "roles": {"nurse", "admin"},
        "requires_room": False,
    },
}


ACTION_TO_EVENT = {
    "check_in": AppointmentEvent.EVENT_CHECKED_IN,
    "doctor_accept": AppointmentEvent.EVENT_DOCTOR_ACCEPTED,
    "transfer_to_room": AppointmentEvent.EVENT_TRANSFERRED_TO_ROOM,
    "room_accept": AppointmentEvent.EVENT_ROOM_ACCEPTED,
    "room_transfer": AppointmentEvent.EVENT_ROOM_TRANSFERRED,
    "complete": AppointmentEvent.EVENT_COMPLETED,
}


ACTION_TO_LOG = {
    "check_in": "checked_in",
    "doctor_accept": "doctor_accepted",
    "transfer_to_room": "transferred_to_room",
    "room_accept": "room_accepted",
    "room_transfer": "room_transferred",
    "complete": "completed_appointment",
}


def _resolve_role(user):
    if not user.is_authenticated:
        return ""
    if user.is_superuser:
        return "admin"

    try:
        return user.profile.role
    except UserProfile.DoesNotExist:
        if user.is_staff:
            return "receptionist"
        return ""


def _assert_permission(user, action):
    rule = ACTION_RULES[action]
    role = _resolve_role(user)
    if role not in rule["roles"]:
        raise PermissionDenied("You do not have permission for this action.")


def _action_description(action, appointment, room):
    patient_name = appointment.patient.full_name
    if action == "check_in":
        return f"Checked in patient: {patient_name}"
    if action == "doctor_accept":
        return f"Doctor accepted patient: {patient_name}"
    if action == "transfer_to_room" and room:
        return f"Doctor transferred patient to {room.name}: {patient_name}"
    if action == "room_accept" and appointment.assigned_room:
        return (
            f"Room accepted patient in {appointment.assigned_room.name}: {patient_name}"
        )
    if action == "room_transfer" and room:
        return f"Room transferred patient to {room.name}: {patient_name}"
    if action == "complete":
        return f"Completed appointment for patient: {patient_name}"
    return f"Updated appointment for patient: {patient_name}"


def _doctor_is_busy(*, exclude_appointment_id=None):
    today = timezone.localdate()
    busy_qs = Appointment.objects.filter(
        status=Appointment.STATUS_WITH_DOCTOR,
        scheduled_at__date=today,
    )
    if exclude_appointment_id:
        busy_qs = busy_qs.exclude(pk=exclude_appointment_id)
    return busy_qs.exists()


def transition_appointment(
    *,
    appointment_id,
    action,
    user,
    room_id=None,
    enforce_doctor_capacity=True,
):
    if action not in ACTION_RULES:
        raise ValidationError("Unknown workflow action.")

    _assert_permission(user, action)
    rule = ACTION_RULES[action]

    with transaction.atomic():
        appointment = (
            Appointment.objects.select_for_update()
            .select_related("patient")
            .get(pk=appointment_id)
        )

        if (
            enforce_doctor_capacity
            and action in {"check_in", "doctor_accept"}
            and _doctor_is_busy(exclude_appointment_id=appointment.id)
        ):
            raise ValidationError(
                "Doctor is currently with another patient. Please wait until the session is finished."
            )

        if appointment.status not in rule["from"]:
            raise ValidationError(
                "Appointment is not in the right state for this action."
            )

        destination_room = None
        if rule["requires_room"]:
            if not room_id:
                raise ValidationError("Please choose a destination room.")

            destination_room = CareRoom.objects.filter(
                pk=room_id, is_active=True
            ).first()
            if destination_room is None:
                raise ValidationError("Selected room is not available.")

            if (
                action == "room_transfer"
                and appointment.assigned_room_id == destination_room.id
            ):
                raise ValidationError("Choose a different room for transfer.")

            appointment.assigned_room = destination_room
        elif action in {"check_in", "doctor_accept"}:
            appointment.assigned_room = None

        if action == "room_accept" and appointment.assigned_room is None:
            raise ValidationError("No room assigned for this appointment yet.")

        previous_status = appointment.status
        appointment.status = rule["to"]
        appointment.save(update_fields=["status", "assigned_room"])

        event = AppointmentEvent.objects.create(
            appointment=appointment,
            event_type=ACTION_TO_EVENT[action],
            from_status=previous_status,
            to_status=appointment.status,
            room=appointment.assigned_room,
            performed_by=user,
        )

        log_action(
            user,
            action=ACTION_TO_LOG[action],
            target_type="appointment",
            target_id=appointment.id,
            description=_action_description(action, appointment, destination_room),
        )

    broadcast_workflow_event(
        appointment=appointment, action=action, actor=user.username
    )
    return appointment, event
