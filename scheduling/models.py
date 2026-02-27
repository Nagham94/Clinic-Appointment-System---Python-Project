from django.db import models
from accounts.models import User

# Create your models here.
"""
doctor weekly schedule:
foreignKey -> User

doctor : schedule
  1    :    M

if doctor is deleted -> all his schedules are deleted
start time & end time -> working hours of each day
appointment duration -> length of each appointment slot in minutes
buffer time -> gap between appointments

"""
class DoctorSchedule(models.Model):

    doctor = models.ForeignKey(User, on_delete=models.CASCADE)
    day_of_week = models.IntegerField()  # days from 0 to 6
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration = models.IntegerField(default=30)
    buffer_time = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.doctor.username} - Day {self.day_of_week}"

"""
schedule exception:
overrides the weekly schedule for specific date (vacation)

doctor : schedule exception days
  1    :    M

date -> date of the exception day
is day off -> true if the doctor is off all day
reason -> optional
"""
class ScheduleException(models.Model):

    doctor = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    is_day_off = models.BooleanField(default=False)
    override_start_time = models.TimeField(blank=True, null=True)
    override_end_time = models.TimeField(blank=True, null=True)
    reason = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.doctor.username} - {self.date}"