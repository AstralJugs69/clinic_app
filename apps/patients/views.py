from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from .models import Patient
from .forms import PatientForm
from apps.accounts.utils import log_action


@login_required
def patient_list(request):
    """List patients with optional search by name or phone."""
    q = request.GET.get("q", "").strip()
    patients = Patient.objects.all().order_by("-created_at")

    if q:
        patients = patients.filter(Q(full_name__icontains=q) | Q(phone__icontains=q))

    return render(
        request,
        "patients/patient_list.html",
        {
            "patients": patients,
            "q": q,
        },
    )


@login_required
def patient_new(request):
    """Create a new patient with PRG pattern."""
    if request.method == "POST":
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save()
            # Log the action
            log_action(
                request,
                action="created_patient",
                target_type="patient",
                target_id=patient.id,
                description=f"Created patient: {patient.full_name}",
            )
            return redirect("patients:detail", pk=patient.id)
    else:
        form = PatientForm()

    return render(request, "patients/patient_form.html", {"form": form})


@login_required
def patient_detail(request, pk):
    """Display patient details."""
    patient = get_object_or_404(Patient, pk=pk)
    return render(request, "patients/patient_detail.html", {"patient": patient})


@login_required
def api_patient_list(request):
    q = request.GET.get("q", "").strip()
    patients = Patient.objects.all().order_by("-created_at")
    if q:
        patients = patients.filter(Q(full_name__icontains=q) | Q(phone__icontains=q))

    payload = [
        {
            "id": patient.id,
            "full_name": patient.full_name,
            "phone": patient.phone,
            "sex": patient.sex,
            "date_of_birth": patient.date_of_birth.isoformat()
            if patient.date_of_birth
            else None,
            "mrn": patient.mrn,
            "address": patient.address,
            "created_at": patient.created_at.isoformat(),
        }
        for patient in patients
    ]
    return JsonResponse(payload, safe=False)


@login_required
def api_patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    payload = {
        "id": patient.id,
        "full_name": patient.full_name,
        "phone": patient.phone,
        "sex": patient.sex,
        "date_of_birth": patient.date_of_birth.isoformat()
        if patient.date_of_birth
        else None,
        "mrn": patient.mrn,
        "address": patient.address,
        "created_at": patient.created_at.isoformat(),
    }
    return JsonResponse(payload)
