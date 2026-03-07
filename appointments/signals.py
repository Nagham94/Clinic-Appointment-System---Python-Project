from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Appointment
from accounts.models import User
from dashboard.models import DashboardStats

@receiver(post_save, sender=Appointment)
def update_appointment_stats(sender, instance, created, **kwargs):
    today = timezone.now().date()
    stats, _ = DashboardStats.objects.get_or_create(date=today)
    
    
    stats.total_appointments = Appointment.objects.filter(created_at__date=today).count()
    stats.completed_appointments = Appointment.objects.filter(status='COMPLETED', updated_at__date=today).count()
    stats.cancelled_appointments = Appointment.objects.filter(status='CANCELLED', updated_at__date=today).count()
    stats.no_show_appointments = Appointment.objects.filter(status='NO_SHOW', updated_at__date=today).count()
    
    
    stats.total_patients = User.objects.filter(role=User.Roles.PATIENT, is_active=True).count()
    stats.total_doctors = User.objects.filter(role=User.Roles.DOCTOR, is_active=True).count()
    
    stats.save()

@receiver(post_save, sender=User)
def update_user_stats(sender, instance, created, **kwargs):
    if created:
        today = timezone.now().date()
        stats, _ = DashboardStats.objects.get_or_create(date=today)
        stats.total_patients = User.objects.filter(role=User.Roles.PATIENT, is_active=True).count()
        stats.total_doctors = User.objects.filter(role=User.Roles.DOCTOR, is_active=True).count()
        stats.save()
