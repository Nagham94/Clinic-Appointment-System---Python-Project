from django.db import models
from django.contrib.auth.models import User

# Create your models here.
"""
doctor weekly schedule:
foreignKey -> User (group = doctor)

doctor : schedule
  1    :    M

if doctor is deleted -> all his schedules are deleted
start time & end time -> working hours of each day
slot duration -> length of each appointment slot in minutes
buffer time -> gap between appointments
"""
class DoctorSchedule(models.Model):

    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'groups__name': 'DOCTOR'}
    )
    day_of_week = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration = models.IntegerField(default=30)
    buffer_time = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.doctor.username} - {self.day_of_week}"

