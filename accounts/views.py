# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import Group
from .forms import PatientRegistrationForm
from .models import Profile

def register_patient(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Assign to Patient group
            patient_group = Group.objects.get(name='patient')
            patient_group.user_set.add(user)

            # Create profile
            Profile.objects.create(user=user, role='patient')

            return redirect('login')

    else:
        form = PatientRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})




def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'accounts/login.html', 
                          {'error': 'Invalid credentials'})

    return render(request, 'accounts/login.html')


def dashboard(request):
    return render(request, 'accounts/dashboard.html')