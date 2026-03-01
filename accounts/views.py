from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
<<<<<<< HEAD
from .forms import RegisterForm, LoginForm, UserProfileUpdateForm, PatientProfileForm, DoctorProfileForm, ReceptionistProfileForm, AdminUserCreationForm
from .models import User, PatientProfile, DoctorProfile, ReceptionistProfile
=======
from .forms import (
    PatientRegistrationForm, AdminUserCreationForm, LoginForm, 
    UserProfileUpdateForm, PatientProfileForm, DoctorProfileForm, ReceptionistProfileForm
)
from .models import User
>>>>>>> authentication-feature
from .decorators import role_required


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
            print(form.errors) 
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


@login_required
@role_required([User.Roles.PATIENT])
def patient_dashboard_view(request):
    return render(request, 'accounts/patient_dashboard.html')


@login_required
@role_required([User.Roles.DOCTOR])
def doctor_dashboard_view(request):
    return render(request, 'accounts/doctor_dashboard.html')


@login_required
@role_required([User.Roles.RECEPTIONIST])
def receptionist_dashboard_view(request):
    return render(request, 'accounts/receptionist_dashboard.html')


@login_required
@role_required([User.Roles.ADMIN])
def admin_dashboard_view(request):
<<<<<<< HEAD
    context = {
        'total_users': User.objects.count(),
        'total_doctors': User.objects.filter(role=User.Roles.DOCTOR).count(),
        'total_receptionists': User.objects.filter(role=User.Roles.RECEPTIONIST).count(),
        'total_patients': User.objects.filter(role=User.Roles.PATIENT).count(),
    }
    return render(request, 'accounts/admin_dashboard.html', context)


@login_required
@role_required([User.Roles.ADMIN])
def admin_user_list_view(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'accounts/admin_user_list.html', {'users': users})


@login_required
@role_required([User.Roles.ADMIN])
def admin_create_user_view(request):
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User {user.username} created successfully as {user.role}.")
            return redirect('admin_user_list')
    else:
        form = AdminUserCreationForm()
    return render(request, 'accounts/admin_create_user.html', {'form': form})
=======
    stats = {
        'total_users': User.objects.count(),
        'patients': User.objects.filter(role=User.Roles.PATIENT).count(),
        'doctors': User.objects.filter(role=User.Roles.DOCTOR).count(),
        'receptionists': User.objects.filter(role=User.Roles.RECEPTIONIST).count(),
    }
    return render(request, 'accounts/admin_dashboard.html', stats)

@login_required
@role_required([User.Roles.ADMIN])
def user_list_view(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'accounts/user_list.html', {'users': users})
>>>>>>> authentication-feature
