from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Appointment
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import get_user_model

# User model import for referencing in views
User = get_user_model()


@login_required
def book_appointment(request):
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        start_datetime = request.POST.get('start_datetime')
        end_datetime = request.POST.get('end_datetime')
        reason = request.POST.get('reason')

        doctor = get_object_or_404(User, id=doctor_id, role='DOCTOR')

        # Check for overlapping appointments(doctor is free during the requested time slot)
        if Appointment.objects.filter(doctor=doctor, start_datetime__lt=end_datetime, end_datetime__gt=start_datetime).exists():
            messages.error(request, 'The selected time slot is not available. Please choose a different time.')
            return redirect('book_appointment')

        appointment = Appointment.objects.create(
            patient=request.user,
            doctor=doctor,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            reason=reason
        )
        messages.success(request, 'Your appointment has been requested successfully.')
        return redirect('patient_dashboard')

    doctors = User.objects.filter(role='DOCTOR')
    return render(request, 'appointments/book_appointment.html', {'doctors': doctors})


