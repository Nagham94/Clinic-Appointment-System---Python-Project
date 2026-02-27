from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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
        User, 
        on_delete=models.CASCADE, 
        related_name='patient_appointments'
    )

    doctor = models.ForeignKey(
        User, 
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
    # Prevents double booking
    class Meta:
        ordering = ['start_datetime']
        unique_together = ('doctor', 'start_datetime')

  
