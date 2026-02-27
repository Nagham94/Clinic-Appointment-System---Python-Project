from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('patient/dashboard/', views.patient_dashboard_view, name='patient_dashboard'),
    path('doctor/dashboard/', views.doctor_dashboard_view, name='doctor_dashboard'),
    path('receptionist/dashboard/', views.receptionist_dashboard_view, name='receptionist_dashboard'),
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('profile/update/', views.update_profile_view, name='update_profile'),
]