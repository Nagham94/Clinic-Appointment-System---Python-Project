from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from appointments.models import Appointment
from .models import Consultation, Prescription, RequestedTest
from .forms import ConsultationForm, PrescriptionFormSet, RequestedTestFormSet

def is_doctor(user):
    return user.is_authenticated and user.role == 'DOCTOR'

@login_required
@user_passes_test(is_doctor)
def create_consultation(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if hasattr(appointment, 'consultation'):
        messages.info(request, "Consultation record already exists for this appointment.")
        return redirect('consultation_detail', consultation_id=appointment.consultation.id)

    if appointment.doctor != request.user:
        messages.error(request, "You can only create consultations for your own appointments.")
        return redirect('doctor_dashboard')

    if request.method == 'POST':
        form = ConsultationForm(request.POST)
        prescription_formset = PrescriptionFormSet(request.POST)
        test_formset = RequestedTestFormSet(request.POST)

        if form.is_valid() and prescription_formset.is_valid() and test_formset.is_valid():
            consultation = form.save(commit=False)
            consultation.appointment = appointment
            consultation.save()

            prescription_formset.instance = consultation
            prescription_formset.save()

            test_formset.instance = consultation
            test_formset.save()

            # Mark appointment as completed
            if appointment.status != 'COMPLETED':
                appointment.status = 'COMPLETED'
                appointment.save()

            messages.success(request, "Consultation record saved successfully.")
            return redirect('consultation_detail', consultation_id=consultation.id)
    else:
        form = ConsultationForm()
        prescription_formset = PrescriptionFormSet()
        test_formset = RequestedTestFormSet()

    context = {
        'form': form,
        'prescription_formset': prescription_formset,
        'test_formset': test_formset,
        'appointment': appointment,
    }
    return render(request, 'medical/create_consultation.html', context)


@login_required
def consultation_detail(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id)
    appointment = consultation.appointment

    # Restrict access
    if request.user.role == 'RECEPTIONIST':
         messages.error(request, "Receptionists do not have access to medical records.")
         return redirect('dashboard_redirect')
         
    if request.user.role == 'PATIENT' and appointment.patient != request.user:
         messages.error(request, "You can only view your own medical records.")
         return redirect('dashboard_redirect')

    if request.user.role == 'DOCTOR' and appointment.doctor != request.user and not request.user.is_superuser:
         messages.error(request, "You can only view medical records for your own patients.")
         return redirect('dashboard_redirect')

    context = {
        'consultation': consultation,
        'appointment': appointment,
        'prescriptions': consultation.prescriptions.all(),
        'tests': consultation.tests.all()
    }
    return render(request, 'medical/consultation_detail.html', context)
