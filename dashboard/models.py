from django.db import models
from accounts.models import User

# Create your models here.
"""
dashboard:
stores summary data for a specific day
total appointments created that day
completed appointments
cancelled appointments
no show appointments -> patients who did not attend
total patients, doctors registered in the system
"""
class DashboardStats(models.Model):

    date = models.DateField()
    total_appointments = models.IntegerField(default=0)
    completed_appointments = models.IntegerField(default=0)
    cancelled_appointments = models.IntegerField(default=0)
    no_show_appointments = models.IntegerField(default=0)
    total_patients = models.IntegerField(default=0)
    total_doctors = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dashboard Stats - {self.date}"