from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import User, PatientProfile, DoctorProfile, ReceptionistProfile

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        # Create corresponding profile
        if instance.role == User.Roles.PATIENT:
            PatientProfile.objects.create(user=instance)
        elif instance.role == User.Roles.DOCTOR:
            DoctorProfile.objects.create(user=instance)
        elif instance.role == User.Roles.RECEPTIONIST:
            ReceptionistProfile.objects.create(user=instance)
        
        # Assign to Group
        group, _ = Group.objects.get_or_create(name=instance.role)
        instance.groups.add(group)
