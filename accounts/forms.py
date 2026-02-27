from django import forms
from django.contrib.auth.models import User
from .models import Profile

class PatientRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        data = super().clean()
        if data['password'] != data.get('confirm_password'):
            raise forms.ValidationError("Passwords do not match.")
        return data