from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone


WORKFLOW_GROUP = "clinicflow.live"


def broadcast_workflow_event(*, appointment, action, actor):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    payload = {
        "appointment_id": appointment.id,
        "patient_id": appointment.patient_id,
        "action": action,
        "status": appointment.status,
        "status_label": appointment.get_status_display(),
        "room": appointment.assigned_room.code if appointment.assigned_room else None,
        "room_name": appointment.assigned_room.name
        if appointment.assigned_room
        else None,
        "actor": actor,
        "timestamp": timezone.now().isoformat(),
    }

    async_to_sync(channel_layer.group_send)(
        WORKFLOW_GROUP,
        {
            "type": "workflow_event",
            "payload": payload,
        },
    )
