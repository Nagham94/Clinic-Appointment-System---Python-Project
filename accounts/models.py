from django.db import models

# Create your models here.
"""
roles -> patient / doctor / receptionist / admin
username & email -> unique
phone -> optional (can be empty)
date of birth -> used to calculate patient age
"""
class User(models.Model):

    ROLE_CHOICES = (
        ('PATIENT', 'Patient'),
        ('DOCTOR', 'Doctor'),
        ('RECEPTIONIST', 'Receptionist'),
        ('ADMIN', 'Admin'),
    )

    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

# return -> username + role -> used in the panel so that each user appears as username(role)
    def __str__(self):
        return f"{self.username} ({self.role})"