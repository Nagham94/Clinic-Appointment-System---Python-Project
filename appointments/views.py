from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Appointment, RescheduleRequest
from scheduling.services import generate_daily_slots
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from django.contrib.auth import get_user_model
from scheduling.services import generate_daily_slots

from sqlite3 import IntegrityError
from django.db import transaction


# User model import for referencing in views
User = get_user_model()


@login_required
def book_appointment(request):
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        reason = request.POST.get('reason')
        start_str = request.POST.get('start_datetime')
        end_str = request.POST.get('end_datetime')

        try:
            start_datetime = timezone.make_aware(datetime.fromisoformat(start_str))
            end_datetime = timezone.make_aware(datetime.fromisoformat(end_str))
        except (ValueError, TypeError):
            messages.error(request, 'Invalid slot selected.')
            return redirect('book_appointment')

        if start_datetime < timezone.now():
            messages.error(request, 'Cannot book an appointment in the past.')
            return redirect('book_appointment')

        doctor = get_object_or_404(User, id=doctor_id, role='DOCTOR')

        # Validate submitted slot exists in generated slots
        available_slots = generate_daily_slots(doctor, start_datetime.date())
        naive_start = start_datetime.replace(tzinfo=None)
        naive_end = end_datetime.replace(tzinfo=None)

        if (naive_start, naive_end) not in available_slots:
            messages.error(request, 'This slot is not available. Please choose another.')
            return redirect('book_appointment')

        # Check patient doesn't have overlapping appointment
        if Appointment.objects.filter(
            patient=request.user,
            status__in=['REQUESTED', 'CONFIRMED'],
            start_datetime__lt=end_datetime,
            end_datetime__gt=start_datetime
        ).exists():
            messages.error(request, 'You already have an appointment during this time.')
            return redirect('book_appointment')

        # Direct DB check to avoid naive/aware mismatch bug in generate_daily_slots
        if Appointment.objects.filter(
            doctor=doctor,
            start_datetime=start_datetime,
            status__in=['REQUESTED', 'CONFIRMED']
        ).exists():
            messages.error(request, 'This slot is no longer available. Please choose another.')
            return redirect('book_appointment')

        # Handle race condition where two patients book the same slot simultaneously
        try:
            with transaction.atomic():
                Appointment.objects.create(
                    patient=request.user,
                    doctor=doctor,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    reason=reason,
                    status='REQUESTED'
                )
        except IntegrityError:
            messages.error(request, 'This slot was just booked by someone else. Please choose another.')
            return redirect('book_appointment')

        messages.success(request, 'Your appointment has been requested successfully.')
        return redirect('patient_dashboard')

    doctors = User.objects.filter(role='DOCTOR')
    return render(request, 'appointments/book_appointment.html', {'doctors': doctors , 'today': timezone.now().date()})

@login_required
def my_appointments(request):
    
    appointments = Appointment.objects.filter(patient=request.user)

    return render(request, 'appointments/my_appointments.html', {
        'appointments': appointments
    })


@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)

    if appointment.status not in ['REQUESTED', 'CONFIRMED']:
        messages.error(request, 'This appointment cannot be cancelled.')
        return redirect('my_appointments')

    if request.method == 'POST':
        appointment.status = 'CANCELLED'
        appointment.save()
        messages.success(request, 'Your appointment has been cancelled successfully.')
        return redirect('my_appointments')

    return render(request, 'appointments/cancel_confirm.html', {'appointment': appointment})

@login_required
def delete_appointment(request, pk):
    appointment = get_object_or_404(Appointment, id=pk)

    # ممكن نضيف حماية زيادة
    if request.user == appointment.patient:
        appointment.delete()
        messages.success(request, "Appointment deleted successfully.")

    return redirect('my_appointments')

@login_required
def reschedule_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # only patient who owns the appointment or receptionist can reschedule
    if request.user != appointment.patient and request.user.role != 'RECEPTIONIST':
        messages.error(request, 'You do not have permission to reschedule this appointment.')
        return redirect('my_appointments')
    
    # only appointments in REQUESTED or CONFIRMED state can be rescheduled
    if appointment.status not in ['REQUESTED', 'CONFIRMED']:
        messages.error(request, 'This appointment cannot be rescheduled.')
        return redirect('my_appointments')
    
    if request.method == 'POST':
        start_date_str = request.POST.get('start_datetime')
        end_date_str = request.POST.get('end_datetime')
        reason = request.POST.get('reason','')
        try:
            start_datetime = timezone.make_aware(datetime.fromisoformat(start_date_str))
            end_datetime = timezone.make_aware(datetime.fromisoformat(end_date_str))
        except (ValueError, TypeError):
            messages.error(request, 'Invalid slot selected.')
            return redirect('reschedule_appointment', appointment_id=appointment_id)
        
        if start_datetime < timezone.now():
            messages.error(request, 'Cannot reschedule to a past time.')
            return redirect('reschedule_appointment', appointment_id=appointment_id)
        
        # validate new slot is available
        available_slots = generate_daily_slots(appointment.doctor, start_datetime.date())
        naive_start = start_datetime.replace(tzinfo=None)
        naive_end = end_datetime.replace(tzinfo=None)

        # Check Patient overlapping appointments
        if Appointment.objects.filter(
            patient=appointment.patient,
            status__in=['REQUESTED', 'CONFIRMED'],
            start_datetime__lt=end_datetime,   # existing starts before new ends
            end_datetime__gt=start_datetime    # existing ends after new starts
        ).exclude(id=appointment.id).exists():
            messages.error(request, 'Patient already has an appointment during this time.')
            return redirect('reschedule_appointment', appointment_id=appointment_id)
        
        # Check doctor slot not already taken (excluding this appointment)
        if Appointment.objects.filter(
            doctor=appointment.doctor,
            start_datetime=start_datetime,
            status__in=['REQUESTED', 'CONFIRMED']
        ).exclude(id=appointment.id).exists():
            messages.error(request, 'This slot is no longer available.')
            return redirect('reschedule_appointment', appointment_id=appointment_id)
        
        try:
            with transaction.atomic():
                # Save Audit Trail
                RescheduleRequest.objects.create(
                    appointment=appointment,
                    changed_by=request.user,
                    old_start_datetime=appointment.start_datetime,
                    old_end_datetime=appointment.end_datetime,
                    new_start_datetime=start_datetime,
                    new_end_datetime=end_datetime,
                    reason=reason
                )

                # Update appointment
                appointment.start_datetime = start_datetime
                appointment.end_datetime = end_datetime
                appointment.status = 'REQUESTED'  # reset to REQUESTED for re-approval
                appointment.save()
        except IntegrityError:
            messages.error(request, 'This slot was just booked by someone else. Please choose another.')
            return redirect('reschedule_appointment', appointment_id=appointment_id)
        
        messages.success(request, 'Your appointment has been rescheduled successfully.')
        return redirect('my_appointments')
    
    # GET — load the form with the doctor pre-selected
    doctors = User.objects.filter(role='DOCTOR')
    return render(request, 'appointments/reschedule_appointment.html', {
        'appointment': appointment,
        'doctors': doctors,
        'today': timezone.now().date(),
    })
    

    


