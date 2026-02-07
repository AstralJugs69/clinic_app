from django import forms
from .models import Patient


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "full_name",
            "phone",
            "sex",
            "date_of_birth",
            "mrn",
            "address",
        ]
        widgets = {
            "full_name": forms.TextInput(
                attrs={"class": "border rounded px-3 py-2 w-full"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "border rounded px-3 py-2 w-full"}
            ),
            "sex": forms.Select(attrs={"class": "border rounded px-3 py-2 w-full"}),
            "date_of_birth": forms.DateInput(
                attrs={"type": "date", "class": "border rounded px-3 py-2 w-full"}
            ),
            "mrn": forms.TextInput(attrs={"class": "border rounded px-3 py-2 w-full"}),
            "address": forms.TextInput(
                attrs={"class": "border rounded px-3 py-2 w-full"}
            ),
        }

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if len(phone) == 10 and not phone.startswith(("09", "+251", "251")):
            raise forms.ValidationError("please enter a valid phone number")

        return phone

    def clean_full_name(self):
        full_name = self.cleaned_data["full_name"]
        if len(full_name) < 5:
            raise forms.ValidationError("the name you entered is too short")
        return full_name
