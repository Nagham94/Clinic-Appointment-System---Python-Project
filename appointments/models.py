from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.
"""
appointment:
lifecycle states of the appointment -> REQUESTED → CONFIRMED → CHECKED_IN → COMPLETED and CANCELLED / NO_SHOW 

patient : appointment
   1    :      M

doctor + start date time -> unique (doctor can't be scheduled twice for the same time)
if patient is deleted -> all his appointments are deleted
if doctor is deleted -> all his appointments are deleted
reason for the appointment -> optional
"""
class Appointment(models.Model):

    class Status(models.TextChoices):
        REQUESTED = 'REQUESTED', 'Requested'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        CHECKED_IN = 'CHECKED_IN', 'Checked In'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        NO_SHOW = 'NO_SHOW', 'No Show'

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_appointments',
        limit_choices_to={'role': 'PATIENT'}
    )

    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_appointments',
        limit_choices_to={'role': 'DOCTOR'}
    )

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.REQUESTED
    )

    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_datetime']
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'start_datetime'],
                name='unique_doctor_start_time'
            )
        ]

    def __str__(self):
        return f"{self.patient} with {self.doctor}"