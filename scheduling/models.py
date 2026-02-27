from django.db import models
from django.conf import settings

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
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'DOCTOR'}
    )

    day_of_week = models.IntegerField()  # 0=monday, 6=sunday
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration = models.PositiveIntegerField(default=30)
    buffer_time = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('doctor', 'day_of_week')

    def __str__(self):
        return f"{self.doctor.username} - Day {self.day_of_week}"

