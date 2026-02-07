from django.urls import path
from . import views

app_name = "appointments"

urlpatterns = [
    path("", views.appointment_today, name="today"),
    path("new/", views.appointment_new, name="new"),
]