from django.urls import path
from . import views

app_name = "appointments"

urlpatterns = [
    path("", views.appointment_today, name="today"),
    path("new/", views.appointment_new, name="new"),
    path("live/frontdesk/", views.frontdesk_feed, name="frontdesk_feed"),
    path("live/frontdesk/intake/", views.frontdesk_intake, name="frontdesk_intake"),
    path("live/doctor/", views.doctor_feed, name="doctor_feed"),
    path("live/room/<str:room_code>/", views.room_feed, name="room_feed"),
    path("<int:pk>/check-in/", views.appointment_check_in, name="check_in"),
    path(
        "<int:pk>/doctor-accept/", views.appointment_doctor_accept, name="doctor_accept"
    ),
    path(
        "<int:pk>/send-room/",
        views.appointment_transfer_to_room,
        name="transfer_to_room",
    ),
    path("<int:pk>/room-accept/", views.appointment_room_accept, name="room_accept"),
    path(
        "<int:pk>/room-transfer/", views.appointment_room_transfer, name="room_transfer"
    ),
    path("<int:pk>/complete/", views.appointment_complete, name="complete"),
]
