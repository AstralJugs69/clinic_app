from django.contrib import admin
from .models import Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "sex", "mrn", "created_at")
    search_fields = ("full_name", "phone", "mrn")