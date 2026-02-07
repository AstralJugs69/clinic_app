from django.urls import path

from apps.appointments.consumers import ClinicFlowConsumer


websocket_urlpatterns = [
    path("ws/flow/", ClinicFlowConsumer.as_asgi()),
]
