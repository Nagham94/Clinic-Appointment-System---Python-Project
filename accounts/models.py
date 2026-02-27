from django.db import models
from django.contrib.auth.models import User

# Create your models here.
"""
roles -> patient / doctor / receptionist / admin
user
phone -> optional (can be empty)
date of birth -> used to calculate patient age
"""
class Profile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)

    # return -> username
    def __str__(self):
        return self.user.username
