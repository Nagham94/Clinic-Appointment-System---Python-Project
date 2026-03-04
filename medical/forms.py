from django import forms
from .models import Consultation, Prescription, RequestedTest
from django.forms import inlineformset_factory

class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['diagnosis', 'notes']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter medical diagnosis here...'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional doctor notes...'}),
        }

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['drug_name', 'dosage', 'duration']
        widgets = {
            'drug_name': forms.TextInput(attrs={'placeholder': 'Drug name'}),
            'dosage': forms.TextInput(attrs={'placeholder': 'Dose (e.g. 500mg)'}),
            'duration': forms.TextInput(attrs={'placeholder': 'Duration (e.g. 5 days)'}),
        }

class RequestedTestForm(forms.ModelForm):
    class Meta:
        model = RequestedTest
        fields = ['test_name']
        widgets = {
            'test_name': forms.TextInput(attrs={'placeholder': 'Test name (e.g. CBC, X-Ray)'}),
        }

PrescriptionFormSet = inlineformset_factory(
    Consultation, Prescription, form=PrescriptionForm, extra=1, can_delete=True
)

RequestedTestFormSet = inlineformset_factory(
    Consultation, RequestedTest, form=RequestedTestForm, extra=1, can_delete=True
)
