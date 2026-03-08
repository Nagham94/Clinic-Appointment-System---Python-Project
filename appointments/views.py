from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Appointment, RescheduleRequest
from scheduling.services import generate_daily_slots
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from django.contrib.auth import get_user_model
from scheduling.services import generate_daily_slots

from django.db import IntegrityError
from django.db import transaction
from django.db.models import Q
import csv
from django.http import HttpResponse
from accounts.decorators import role_required
from accounts.models import User



# User model import for referencing in views
User = get_user_model()


@login_required
@role_required(["PATIENT"])
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
    return render(request, 'appointments/book_appointment.html', {'doctors': doctors , 'today': timezone.now().date(),  'now': timezone.localtime().time()})

@login_required
@role_required(["PATIENT"])
def book_appointment_from_DoctorList(request, doctor_id):
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

    context = {
        "doctors": doctors,
        "selected_doctor_id": doctor_id
    }
    # return render(request, "appointments/book_appointment.html", {"doctor": doctors})
    return render(request, "appointments/book_appointment.html", context)


@login_required
@role_required(["PATIENT"])
def my_appointments(request):
    appointments = Appointment.objects.filter(
        patient=request.user
    ).order_by('-start_datetime')

    return render(request, 'appointments/my_appointments.html', {
        'appointments': appointments
    })


@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Allow cancellation by patient, receptionist, or patient's doctor
    is_patient = appointment.patient == request.user
    is_staff = request.user.role in ['RECEPTIONIST', 'DOCTOR']  # doctors can also cancel on behalf of patients
    
    if not (is_patient or is_staff):
        messages.error(request, 'You do not have permission to cancel this appointment.')
        return redirect('my_appointments')

    if appointment.status not in ['REQUESTED', 'CONFIRMED']:
        messages.error(request, 'This appointment cannot be cancelled.')
        return redirect('my_appointments' if is_patient else 'dashboard_redirect')

    if request.method == 'POST':
        appointment.status = 'CANCELLED'
        appointment.save()
        messages.success(request, 'Appointment has been cancelled successfully.')
        return redirect('my_appointments' if is_patient else 'dashboard_redirect')

    return render(request, 'appointments/cancel_confirm.html', {'appointment': appointment})

@login_required
def delete_appointment(request, pk):
    appointment = get_object_or_404(Appointment, id=pk)

    if appointment.status not in ['CANCELLED', 'NO_SHOW']:
        messages.error(request, 'Only cancelled or no-show appointments can be deleted.')
        return redirect('my_appointments')

    if request.user == appointment.patient:
        appointment.delete()
        messages.success(request, "Appointment deleted successfully.")

    return redirect('my_appointments')


@login_required
@role_required(["PATIENT", "RECEPTIONIST"])
def reschedule_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    is_receptionist = request.user.role == 'RECEPTIONIST'
    redirect_target =  ('queue_manager' if is_receptionist else 'my_appointments')

    # only patient who owns the appointment or receptionist can reschedule
    if request.user != appointment.patient and request.user.role != 'RECEPTIONIST':
        messages.error(request, 'You do not have permission to reschedule this appointment.')
        return redirect(redirect_target)
    
    # only appointments in REQUESTED or CONFIRMED state can be rescheduled
    if appointment.status not in ['REQUESTED', 'CONFIRMED']:
        messages.error(request, 'This appointment cannot be rescheduled.')
        return redirect(redirect_target)
    
    if request.method == 'POST':
        start_date_str = request.POST.get('start_datetime')
        end_date_str = request.POST.get('end_datetime')
        reason = request.POST.get('reason','')

        if not start_date_str or not end_date_str:
            messages.error(request, 'Please select a time slot.')
            return redirect('reschedule_appointment', appointment_id=appointment_id)
    
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
        return redirect(redirect_target)
    
    # GET — load the form with the doctor pre-selected
    doctors = User.objects.filter(role='DOCTOR')
    return render(request, 'appointments/reschedule_appointment.html', {
        'appointment': appointment,
        'doctors': doctors,
        'today': timezone.now().date(),
    })


@login_required
@role_required(["RECEPTIONIST", "DOCTOR"])
def confirm_appointment(request, pk):
    appointment = get_object_or_404(Appointment, id=pk)

    is_staff = request.user.role in ['RECEPTIONIST', 'DOCTOR']  # doctors can also cancel on behalf of patients
    if not is_staff:
        messages.error(request, 'You do not have permission to confirm this appointment.')
        return redirect('dashboard_redirect')

    if appointment.status == 'REQUESTED':
        appointment.status = 'CONFIRMED'
        appointment.save()
        messages.success(request, "Appointment Confirmed Successfully.")

    return redirect('queue_manager')

@login_required
@role_required(["DOCTOR", "RECEPTIONIST", "ADMIN"])
def show_confirmed_appointments(request):
    """
    Shows all CONFIRMED appointments.
    Doctors only see their own; receptionists/admins see all.
    Defaults to today's date if no date filter is provided.
    """
    qs = Appointment.objects.select_related('patient', 'doctor').filter(status='CONFIRMED')

    if request.user.role == 'DOCTOR':
        qs = qs.filter(doctor=request.user)

    selected_date = request.GET.get('date')

    # Default to today if no date provided
    if not selected_date:
        selected_date = timezone.localtime().date().isoformat()

    try:
        date_obj = datetime.fromisoformat(selected_date).date()
        qs = qs.filter(start_datetime__date=date_obj)
    except ValueError:
        messages.warning(request, 'Invalid date format.')

    return render(request, 'appointments/confirmed_appointments.html', {
        'appointments': qs.order_by('start_datetime')[:200],
        'selected_date': selected_date,
    })

@login_required
@role_required(["RECEPTIONIST", "DOCTOR"])
def mark_no_show(request, pk):
    """
    Receptionist and Doctor marks an appointment as No Show.
    Only CONFIRMED appointments past their start time can be marked as no show.
    """
    appointment = get_object_or_404(Appointment, id=pk)

    if appointment.status != 'CONFIRMED':
        messages.error(request, 'Only confirmed appointments can be marked as no show.')
        return redirect(request.META.get('HTTP_REFERER') or 'confirmed_appointments')

    if appointment.start_datetime >= timezone.localtime():
        messages.error(request, 'Cannot mark as no show before the appointment time.')
        return redirect(request.META.get('HTTP_REFERER') or 'confirmed_appointments')

    appointment.status = 'NO_SHOW'
    appointment.save()

    messages.warning(
        request,
        f'{appointment.patient.get_full_name() or appointment.patient.username} has been marked as no show.'
    )
    
    return redirect(request.META.get('HTTP_REFERER') or 'confirmed_appointments')

@login_required
@role_required(["RECEPTIONIST", "DOCTOR"])
def checkin_patient(request, pk):
    """
    Receptionist checks in a patient.
    Only CONFIRMED appointments can be checked in.
    Sets checked_in_at timestamp and changes status to CHECKED_IN.
    """
    appointment = get_object_or_404(Appointment, id=pk)

    if appointment.status != 'CONFIRMED':
        messages.error(request, 'Only confirmed appointments can be checked in.')
        return redirect(request.META.get('HTTP_REFERER') or 'confirmed_appointments')

    appointment.status = 'CHECKED_IN'
    appointment.checked_in_at = timezone.now()
    appointment.save()
    messages.success(
        request,
        f'{appointment.patient.get_full_name() or appointment.patient.username} has been checked in successfully.'
    )
    return redirect(request.META.get('HTTP_REFERER') or 'confirmed_appointments')

@login_required
@role_required(["DOCTOR"])
def completed_appointments(request):
    """
    Shows all COMPLETED appointments.
    Doctors see their own; patients see their own.
    """
    if request.user.role == 'DOCTOR':
        qs = Appointment.objects.select_related('patient', 'doctor').filter(
            status='COMPLETED',
            doctor=request.user
        ).order_by('-start_datetime')
        template = 'appointments/completed_appointments.html'

    else:  # PATIENT
        qs = Appointment.objects.select_related('patient', 'doctor').filter(
            status='COMPLETED',
            patient=request.user
        ).order_by('-start_datetime')
        template = 'appointments/patient_completed_appointments.html'

    return render(request, template, {'appointments': qs})


"""
search and filter view for staff to manage appointments, with access control so doctors only see their own appointments but receptionists and admins can see all.
Supports filtering by status, date, doctor, patient and a search box that looks up patient
"""
@login_required
@role_required(["DOCTOR", "RECEPTIONIST", "ADMIN"]) 
# to display all appointments
def staff_appointments(request):
    # join with doctor and patient to display their names and all appointments
    qs = Appointment.objects.select_related('patient', 'doctor').all()

    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    doctor_id = request.GET.get('doctor')
    patient_id = request.GET.get('patient')
    q = request.GET.get('q')
    
    # filter by status -> confirmed, cancelled, no-show, .....
    if status:
        qs = qs.filter(status=status)

    # date range filter -> filter by start/end date
    try:
        if start_date:
            qs = qs.filter(start_datetime__date__gte=datetime.fromisoformat(start_date).date())
        if end_date:
            qs = qs.filter(start_datetime__date__lte=datetime.fromisoformat(end_date).date())
    except ValueError:
        messages.warning(request, 'Invalid date format. Use YYYY-MM-DD.')
    
    # filter by doctor or patient id 
    if doctor_id:
        qs = qs.filter(doctor__id=doctor_id)
    if patient_id:
        qs = qs.filter(patient__id=patient_id)

    # If the logged in user is a doctor, only show their appointments
    if request.user.role == 'DOCTOR':
        qs = qs.filter(doctor=request.user)
        doctor_id = str(request.user.id)
    
    # search box to look up patient by name, also allow searching by appointment id
    if q:
        q = q.strip()
        filters = Q(patient__username__icontains=q) | Q(patient__first_name__icontains=q) | Q(patient__last_name__icontains=q)
        if q.isdigit():
            filters |= Q(id=int(q))
        qs = qs.filter(filters)
    
    users = get_user_model().objects.filter(Q(role='DOCTOR') | Q(role='PATIENT'))
    doctors = users.filter(role='DOCTOR')
    patients = users.filter(role='PATIENT')

    context = {
        'appointments': qs.order_by('-start_datetime')[:200],
        'doctors': doctors,
        'patients': patients,
        'statuses': Appointment.Status,
        'selected': {
            'status': status,
            'start_date': start_date,
            'end_date': end_date,
            'doctor_id': doctor_id,
            'patient_id': patient_id,
            'q': q,
        }
    }

    return render(request, 'appointments/staff_appointments.html', context)

@login_required
def my_appointments(request):
    appointments = Appointment.objects.filter(patient=request.user)

    return render(request, 'appointments/my_appointments.html', {
        'appointments': appointments
    })

def doctor_list_view(request):
    doctors = User.objects.filter(role='DOCTOR')

    context = {
        'doctors': doctors
    }

    return render(request, 'appointments/doctor_list.html', context)

@login_required
@role_required(["ADMIN"])
def export_appointments_csv(request):
    import csv
    from django.http import HttpResponse
    
    appointments = Appointment.objects.all().select_related('patient', 'doctor').order_by('-start_datetime')
    count = appointments.count()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="appointments_{timezone.now().date()}.csv"'
    

    response['X-Appointment-Count'] = str(count)

    writer = csv.writer(response)
    writer.writerow(['ID', 'Patient', 'Doctor', 'Start', 'End', 'Status', 'Reason'])

    for appt in appointments:
        try:
            start_str = appt.start_datetime.strftime('%Y-%m-%d %H:%M') if appt.start_datetime else "N/A"
            end_str = appt.end_datetime.strftime('%Y-%m-%d %H:%M') if appt.end_datetime else "N/A"
            writer.writerow([
                appt.id,
                appt.patient.username if appt.patient else "Deleted User",
                appt.doctor.username if appt.doctor else "Deleted Doctor",
                start_str,
                end_str,
                appt.get_status_display(),
                appt.reason or ""
            ])
        except Exception as e:
            writer.writerow([appt.id, "ERROR", str(e)])

    return response
