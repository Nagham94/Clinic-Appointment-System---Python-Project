from django.db import models
from appointments.models import Appointment

# Create your models here.
"""
consultation:
created after completed appointment

consultation : appointment
     1       :      1

if the appointment is deleted -> the consultation is deleted
stores the medical diagnosis -> no limits
notes written by the doctor -> optional (can be empty)
"""
class Consultation(models.Model):

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE
    )
    diagnosis = models.TextField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Consultation {self.id}"

"""
prescription:
medication item given during a consultation

consultation : prescription
     1       :      M
     
if consultation is deleted -> all prescriptions are deleted
add name, dosage, duration of the medicine
"""
class Prescription(models.Model):

    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE
    )
    drug_name = models.CharField(max_length=100)
    dosage = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)

    def __str__(self):
        return self.drug_name

"""
requested tests:
tests requested by the doctor

consultation : requested tests
    1        :       M
    
add the name of the test -> the same test can be requested in more that one consultation
"""
class RequestedTest(models.Model):

    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    test_name = models.CharField(max_length=150)

    def __str__(self):
        return self.test_name