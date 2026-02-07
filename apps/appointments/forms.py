from django import forms
from .models import Appointment
from apps.patients.models import Patient


class AppointmentForm(forms.ModelForm):
    scheduled_at = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={
                "type": "datetime-local",
                "class": "border rounded px-3 py-2 w-full",
            },
        ),
    )

    class Meta:
        model = Appointment
        fields = [
            "patient",
            "scheduled_at",
            "duration_minutes",
            "reason",
        ]
        widgets = {
            "patient": forms.Select(attrs={"class": "border rounded px-3 py-2 w-full"}),
            "duration_minutes": forms.NumberInput(
                attrs={
                    "class": "border rounded px-3 py-2 w-full",
                    "min": "5",
                    "max": "120",
                }
            ),
            "reason": forms.TextInput(
                attrs={
                    "class": "border rounded px-3 py-2 w-full",
                    "placeholder": "Reason for visit",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["patient"].queryset = Patient.objects.order_by("full_name")
