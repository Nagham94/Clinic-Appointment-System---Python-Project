from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    Roles_Choice = [
        ('Doctor', 'doctor'),
        ('Patient', 'patient'),
        ('Receptionist', 'receptionist'),
        ('Admin', 'admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Roles_Choice)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"
    


    