from django.urls import path
from . import views

urlpatterns = [
    path('schedules/', views.DoctorScheduleListView.as_view(), name='schedule_list'),
    path('schedules/create/', views.DoctorScheduleCreateView.as_view(), name='schedule_create'),
    path('schedules/<int:pk>/edit/', views.DoctorScheduleUpdateView.as_view(), name='schedule_update'),
    path('schedules/<int:pk>/delete/', views.DoctorScheduleDeleteView.as_view(), name='schedule_delete'),
    path('exceptions/', views.ScheduleExceptionListView.as_view(), name='exception_list'),
    path('exceptions/create/', views.ScheduleExceptionCreateView.as_view(), name='exception_create'),
    path('exceptions/<int:pk>/edit/', views.ScheduleExceptionUpdateView.as_view(), name='exception_update'),
    path('exceptions/<int:pk>/delete/', views.ScheduleExceptionDeleteView.as_view(), name='exception_delete'),
    path('api/available-slots/', views.AvailableSlotsView.as_view(), name='available_slots'),
    
    # doctor personal schedule view
    path('my-schedule/', views.doctor_weekly_schedule, name='doctor_weekly_schedule'),
]