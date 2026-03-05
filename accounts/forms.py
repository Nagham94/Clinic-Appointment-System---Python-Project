from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, PatientProfile, DoctorProfile, ReceptionistProfile
from django.contrib.auth import authenticate
from django.utils import timezone
import re

class PatientRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.role = User.Roles.PATIENT
        if commit:
            user.save()
        return user

class AdminUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.Roles.choices, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Username"
        self.fields['first_name'].label = "First Name"
        self.fields['last_name'].label = "Last Name"
        self.fields['email'].label = "Email Address"
        self.fields['role'].label = "Account Role"

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username or Email")
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        username_or_email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        user = authenticate(username=username_or_email, password=password)
        if not user:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        if not user:
            raise forms.ValidationError("Invalid username/email or password")
        self.user_cache = user
        return self.cleaned_data

class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = ['phone', 'date_of_birth', 'address']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    # phone number validation
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()

        if phone:
            egyptian_phone_regex = re.compile(
                r'^(\+20|0020)?0(10|11|12|15)\d{8}$'
            )
            cleaned_phone = re.sub(r'[\s\-]', '', phone)
            if not egyptian_phone_regex.match(cleaned_phone):
                raise forms.ValidationError(
                    "Enter a valid Egyptian phone number. "
                    "Valid Egyptian operators start with 010, 011, 012, or 015, "
                    "e.g. 01012345678 or +201012345678."
                )

        return phone

    # dob validation
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:  
            today = timezone.now().date()

            if dob > today:
                raise forms.ValidationError(
                    "Date of birth cannot be in the future."
                )

        return dob

class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = ['specialization', 'bio']

class ReceptionistProfileForm(forms.ModelForm):
    class Meta:
        model = ReceptionistProfile
        fields = []
