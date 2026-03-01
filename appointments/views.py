from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Appointment
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from django.contrib.auth import get_user_model

# User model import for referencing in views
User = get_user_model()


@login_required
def book_appointment(request):
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        reason = request.POST.get('reason')

        try:
            start_datetime = timezone.make_aware(datetime.fromisoformat(request.POST.get('start_datetime')))
            end_datetime = timezone.make_aware(datetime.fromisoformat(request.POST.get('end_datetime')))
        except ValueError:
            messages.error(request, 'Invalid date format. Please enter valid date and time.')
            return redirect('book_appointment')
        
        duration = end_datetime - start_datetime
        
        # Validate Time
        if start_datetime >= end_datetime:
            messages.error(request, 'End time must be after start time.')
            return redirect('book_appointment')

        if start_datetime < timezone.now():
            messages.error(request, 'Cannot book an appointment in the past.')
            return redirect('book_appointment')

        if not (13 <= start_datetime.hour < 23):
            messages.error(request, 'Appointments must be between 1:00 PM and 11:00 PM.')
            return redirect('book_appointment')
        
        if duration.total_seconds() > 3600:
            messages.error(request, 'Appointment duration cannot exceed 1 hour.')
            return redirect('book_appointment')

        
        doctor = get_object_or_404(User, id=doctor_id, role='DOCTOR')
        # Check doctor overlap
        if Appointment.objects.filter(
            doctor=doctor,
            start_datetime__lt=end_datetime,
            end_datetime__gt=start_datetime
        ).exists():
            messages.error(request, 'This time slot is not available. Please choose a different time.')
            return redirect('book_appointment')
        
        # Check patient overlap
        if Appointment.objects.filter(
            patient=request.user,
            status__in=['REQUESTED', 'CONFIRMED'],
            start_datetime__lt=end_datetime,
            end_datetime__gt=start_datetime
        ).exists():
            messages.error(request, 'You already have an appointment during this time.')
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





@login_required
def my_appointments(request):
    appointments = Appointment.objects.filter(patient=request.user)

    return render(request, 'appointments/my_appointments.html', {
        'appointments': appointments
    })