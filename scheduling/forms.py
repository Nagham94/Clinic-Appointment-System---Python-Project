from django import forms
from .models import DoctorSchedule, ScheduleException
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class DoctorScheduleForm(forms.ModelForm):
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    day_of_week = forms.ChoiceField(
        choices=DAY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = DoctorSchedule
        fields = ['doctor', 'day_of_week', 'start_time', 'end_time', 'slot_duration', 'buffer_time']
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'slot_duration': forms.Select(
                choices=[(15, '15 minutes'), (30, '30 minutes')],
                attrs={'class': 'form-select'}
            ),
            'buffer_time': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 30}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['doctor'].queryset = User.objects.filter(role='DOCTOR')
        self.fields['doctor'].label_from_instance = lambda obj: f"Dr. {obj.get_full_name() or obj.username}"

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        doctor = cleaned_data.get('doctor')
        day_of_week = cleaned_data.get('day_of_week')

        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("Start time must be before end time.")

        if doctor and day_of_week is not None:
            day_of_week = int(day_of_week)
            overlapping = DoctorSchedule.objects.filter(
                doctor=doctor,
                day_of_week=day_of_week,
            )
            if self.instance and self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)

            if overlapping.exists():
                existing = overlapping.first()
                if start_time and end_time:
                    if start_time < existing.end_time and end_time > existing.start_time:
                        raise forms.ValidationError(
                            f"This overlaps with an existing schedule for this doctor on this day "
                            f"({existing.start_time.strftime('%H:%M')} - {existing.end_time.strftime('%H:%M')})."
                        )

        return cleaned_data


class ScheduleExceptionForm(forms.ModelForm):
    class Meta:
        model = ScheduleException
        fields = ['doctor', 'date', 'is_day_off', 'override_start_time', 'override_end_time', 'reason']
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'is_day_off': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'override_start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'override_end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'reason': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Vacation, Conference...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['doctor'].queryset = User.objects.filter(role='DOCTOR')
        self.fields['doctor'].label_from_instance = lambda obj: f"Dr. {obj.get_full_name() or obj.username}"
        self.fields['reason'].required = False

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        doctor = cleaned_data.get('doctor')
        is_day_off = cleaned_data.get('is_day_off')
        override_start = cleaned_data.get('override_start_time')
        override_end = cleaned_data.get('override_end_time')
        reason = cleaned_data.get('reason')

        if date and date < timezone.now().date():
            raise forms.ValidationError("Cannot create an exception for a past date.")

        if doctor and date:
            existing = ScheduleException.objects.filter(
                doctor=doctor,
                date=date,
            )
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise forms.ValidationError(
                    f"An exception already exists for this doctor on {date.strftime('%Y-%m-%d')}. "
                    f"Please edit the existing exception instead."
                )

        if not is_day_off:
            if override_start and override_end:
                if override_start >= override_end:
                    raise forms.ValidationError("Override start time must be before override end time.")
            elif override_start or override_end:
                raise forms.ValidationError(
                    "Both override start and end times are required if not a full day off."
                )

        if is_day_off:
            if not reason:
                self.add_error('reason', 'Reason is required when marking a full day off.')
            cleaned_data['override_start_time'] = None
            cleaned_data['override_end_time'] = None

        return cleaned_data