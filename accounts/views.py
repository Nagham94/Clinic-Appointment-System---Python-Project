# from datetime import timezone

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .forms import (
    PatientRegistrationForm, AdminUserCreationForm, LoginForm, 
    UserProfileUpdateForm, PatientProfileForm, DoctorProfileForm, ReceptionistProfileForm
)
from .models import User, PatientProfile, DoctorProfile, ReceptionistProfile
from appointments.models import Appointment
from .decorators import role_required
from django.utils import timezone

def register_view(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Account created successfully for {user.username}! Please log in.")
            return redirect('login')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        form = PatientRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
@role_required([User.Roles.ADMIN])
def admin_register_view(request):
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User {user.username} (Role: {user.role}) created successfully!")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Failed to create user. Please check the form.")
    else:
        form = AdminUserCreationForm()
    return render(request, 'accounts/admin_register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect_role_dashboard(user)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been successfully logged out.")
    return redirect('login')


def redirect_role_dashboard(user):
    if user.role == User.Roles.PATIENT:
        return redirect('patient_dashboard')  
    elif user.role == User.Roles.DOCTOR:
        return redirect('doctor_dashboard')
    elif user.role == User.Roles.RECEPTIONIST:
        return redirect('receptionist_dashboard')
    elif user.role == User.Roles.ADMIN:
        return redirect('admin_dashboard')
    else:
        return redirect('login')


@login_required
def dashboard_redirect(request):
    return redirect_role_dashboard(request.user)


@login_required
def update_profile_view(request):
    user = request.user
    
    # Ensure the corresponding profile exists
    if user.role == User.Roles.PATIENT:
        profile_instance, _ = PatientProfile.objects.get_or_create(user=user)
        ProfileFormClass = PatientProfileForm
    elif user.role == User.Roles.DOCTOR:
        profile_instance, _ = DoctorProfile.objects.get_or_create(user=user)
        ProfileFormClass = DoctorProfileForm
    elif user.role == User.Roles.RECEPTIONIST:
        profile_instance, _ = ReceptionistProfile.objects.get_or_create(user=user)
        ProfileFormClass = ReceptionistProfileForm
    else:
        profile_instance = None
        ProfileFormClass = None

    if request.method == 'POST':
        user_form = UserProfileUpdateForm(request.POST, instance=user)
        profile_form = ProfileFormClass(request.POST, instance=profile_instance) if ProfileFormClass else None
        
        if user_form.is_valid() and (profile_form is None or profile_form.is_valid()):
            user_form.save()
            if profile_form:
                profile_form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('dashboard_redirect')
    else:
        user_form = UserProfileUpdateForm(instance=user)
        profile_form = ProfileFormClass(instance=profile_instance) if ProfileFormClass else None
        
    return render(request, 'accounts/update_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

# shahd new
@login_required
@role_required([User.Roles.PATIENT])
def patient_dashboard_view(request):
    doctors = User.objects.filter(role='DOCTOR')

    context = {
        "doctors": doctors
    }

    return render(request, "accounts/patient_dashboard.html", context)
# def patient_dashboard_view(request):
#     return render(request, 'accounts/patient_dashboard.html')


@login_required
@role_required([User.Roles.DOCTOR])
def doctor_dashboard_view(request):
    appointments = Appointment.objects.filter(
        doctor=request.user
    ).order_by('start_datetime')

    context = {
        'appointments': appointments,
        'now': timezone.now()
    }
    return render(request, 'accounts/doctor_dashboard.html')


@login_required
@role_required([User.Roles.RECEPTIONIST])
def receptionist_dashboard_view(request):
    appointments = Appointment.objects.all().order_by('start_datetime')

    context = {
        'appointments': appointments,
        'now': timezone.now()
    }
    return render(request, 'accounts/receptionist_dashboard.html')



def queue_manager_view(request):

    requested_appointments = Appointment.objects.filter(
        status='REQUESTED'
    ).order_by('start_datetime')

    if request.user.is_authenticated and request.user.role == 'DOCTOR':
        requested_appointments = requested_appointments.filter(doctor=request.user)

    context = {
        'appointments': requested_appointments
    }

    return render(request, 'accounts/queue_manager.html', context)

@login_required
@role_required([User.Roles.ADMIN])
def admin_dashboard_view(request):
    from dashboard.models import DashboardStats
    from django.utils import timezone
    
    today = timezone.now().date()
    daily_stats, created = DashboardStats.objects.get_or_create(date=today)
    
    # If it's a new stats object or we want to ensure it's fresh, we can recalculate:
    if created or daily_stats.total_appointments == 0:
        from appointments.models import Appointment
        daily_stats.total_appointments = Appointment.objects.filter(created_at__date=today).count()
        daily_stats.completed_appointments = Appointment.objects.filter(status='COMPLETED', updated_at__date=today).count()
        daily_stats.cancelled_appointments = Appointment.objects.filter(status='CANCELLED', updated_at__date=today).count()
        daily_stats.no_show_appointments = Appointment.objects.filter(status='NO_SHOW', updated_at__date=today).count()
        daily_stats.total_patients = User.objects.filter(role=User.Roles.PATIENT, is_active=True).count()
        daily_stats.total_doctors = User.objects.filter(role=User.Roles.DOCTOR, is_active=True).count()
        daily_stats.save()
    
    # Get historical stats for a simple chart (last 7 days)
    history = DashboardStats.objects.all().order_by('-date')[:7]
    
    context = {
        'total_users': User.objects.count(),
        'patients': User.objects.filter(role=User.Roles.PATIENT).count(),
        'doctors': User.objects.filter(role=User.Roles.DOCTOR).count(),
        'receptionists': User.objects.filter(role=User.Roles.RECEPTIONIST).count(),
        'stat_total': daily_stats.total_appointments,
        'stat_completed': daily_stats.completed_appointments,
        'stat_cancelled': daily_stats.cancelled_appointments,
        'stat_no_show': daily_stats.no_show_appointments,
        'history': history,
    }
    return render(request, 'accounts/admin_dashboard.html', context)


@login_required
@role_required([User.Roles.ADMIN])
def user_list_view(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'accounts/user_list.html', {'users': users, 'roles': User.Roles.choices})


@login_required
@role_required([User.Roles.ADMIN])
@require_POST
def toggle_user_status(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
    else:
        target_user.is_active = not target_user.is_active
        target_user.save()
        status = "activated" if target_user.is_active else "deactivated"
        messages.success(request, f"User {target_user.username} has been {status}.")
    return redirect('user_list')


@login_required
@role_required([User.Roles.ADMIN])
@require_POST
def change_user_role(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    new_role = request.POST.get('role')
    
    if new_role in User.Roles.values:
        target_user.role = new_role
        target_user.save()
        messages.success(request, f"Role for {target_user.username} changed to {target_user.get_role_display()}.")
    else:
        messages.error(request, "Invalid role selected.")
    
    return redirect('user_list')

@login_required
@role_required([User.Roles.ADMIN])
def admin_edit_user(request, user_id):
    from .forms import AdminUserProfileUpdateForm
    target_user = get_object_or_404(User, id=user_id)
    
    # Identify profile and form class
    if target_user.role == User.Roles.PATIENT:
        profile_instance, _ = PatientProfile.objects.get_or_create(user=target_user)
        ProfileFormClass = PatientProfileForm
    elif target_user.role == User.Roles.DOCTOR:
        profile_instance, _ = DoctorProfile.objects.get_or_create(user=target_user)
        ProfileFormClass = DoctorProfileForm
    elif target_user.role == User.Roles.RECEPTIONIST:
        profile_instance, _ = ReceptionistProfile.objects.get_or_create(user=target_user)
        ProfileFormClass = ReceptionistProfileForm
    else:
        profile_instance = None
        ProfileFormClass = None

    if request.method == 'POST':
        user_form = AdminUserProfileUpdateForm(request.POST, instance=target_user)
        profile_form = ProfileFormClass(request.POST, instance=profile_instance) if ProfileFormClass else None
        
        if user_form.is_valid() and (profile_form is None or profile_form.is_valid()):
            user_form.save()
            if profile_form:
                profile_form.save()
            messages.success(request, f"User {target_user.username} has been updated successfully.")
            return redirect('user_list')
    else:
        user_form = AdminUserProfileUpdateForm(instance=target_user)
        profile_form = ProfileFormClass(instance=profile_instance) if ProfileFormClass else None
        
    return render(request, 'accounts/admin_edit_user.html', {
        'target_user': target_user,
        'user_form': user_form,
        'profile_form': profile_form
    })
