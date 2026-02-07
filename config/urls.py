"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from apps.accounts.views import StaffLoginView, logout_view
from apps.patients import views as patient_views
from apps.appointments import views as appointment_views
from apps.accounts import views as account_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", StaffLoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
    path("", RedirectView.as_view(url="/patients/", permanent=False)),
    path("patients/", include("apps.patients.urls")),
    path("appointments/", include("apps.appointments.urls")),
    path("activity/", account_views.activity, name="activity"),
    path("accounts/", include("apps.accounts.urls")),
    path("api/patients/", patient_views.api_patient_list, name="api-patient-list"),
    path(
        "api/patients/<int:pk>/",
        patient_views.api_patient_detail,
        name="api-patient-detail",
    ),
    path(
        "api/appointments/today/",
        appointment_views.api_today_appointments,
        name="api-appointments-today",
    ),
    path("api/logs/", account_views.api_logs, name="api-logs"),
]
