from django.shortcuts import render
from django.db.models import Q
from django.http import HttpResponse
from .models import Patient

def patient_list(request):
    q = request.GET.get("q", "")
    patients = Patient.objects.filter(
        Q(full_name__icontains=q) | Q(phone__icontains=q)
    ).order_by("-created_at") #filtering has never been so easy
    return render(
        request,
        "patients/patient_list.html",
        {
          "patients": patients,
          "q": q,  
        }
    )

def patient_new(request):
    return HttpResponse("yeah")

def patient_detail(request):
    return HttpResponse("smt")
# Create your views here.
