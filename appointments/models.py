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

    STATUS_CHOICES = [
        ('REQUESTED', 'Requested'),
        ('CONFIRMED', 'Confirmed'),
        ('CHECKED_IN', 'Checked In'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show'),
    ]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_appointments'
    )

    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_appointments'
    )

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='REQUESTED'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['start_datetime']
        unique_together = ('doctor', 'start_datetime')

    def __str__(self):
        return f"{self.patient.username} with {self.doctor.username}"