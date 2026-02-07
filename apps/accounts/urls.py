from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.activity, name="activity"),
    path("profile/", views.profile, name="profile"),
    path("staff/", views.staff_list, name="staff_list"),
]
