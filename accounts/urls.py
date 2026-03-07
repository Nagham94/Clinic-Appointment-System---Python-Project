from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('patient/dashboard/', views.patient_dashboard_view, name='patient_dashboard'),
    path('doctor/dashboard/', views.doctor_dashboard_view, name='doctor_dashboard'),
    path('receptionist/dashboard/', views.receptionist_dashboard_view, name='receptionist_dashboard'),
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    
    path('admin/register/', views.admin_register_view, name='admin_register'),
    path('admin/users/', views.user_list_view, name='user_list'),
    path('admin/users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('admin/users/<int:user_id>/change-role/', views.change_user_role, name='change_user_role'),
    path('admin/users/<int:user_id>/edit/', views.admin_edit_user, name='admin_edit_user'),
    
    path('profile/update/', views.update_profile_view, name='update_profile'),

   
    path('password-change/', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change.html'), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name='password_change_done'),



    
    path('receptionist/queue/', views.queue_manager_view, name='queue_manager'),

]