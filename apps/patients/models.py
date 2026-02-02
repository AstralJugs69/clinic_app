from django.db import models

class Patient(models.Model):
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30)
    sex = models.CharField(
        max_length=10,
        choices=[
            ("M", "Male"),
            ("F", "Female")
        ],
    )
    date_of_birth = models.DateField(null=True, blank=True)
    mrn = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"{self.full_name} ({self.phone})"