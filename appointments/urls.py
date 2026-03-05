from django.urls import path
from . import views
# from .views import my_appointments

urlpatterns = [
    path('book/', views.book_appointment, name='book_appointment'),
    path('appointment/<int:pk>/delete/', views.delete_appointment, name='delete_appointment'),
    path('my-appointments/', views.my_appointments, name='my_appointments'),
    path('cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('<int:appointment_id>/reschedule/', views.reschedule_appointment, name='reschedule_appointment'),
    path('appointment/<int:pk>/no-show/', views.mark_no_show, name='mark_no_show'),
    path('appointment/<int:pk>/confirm/', views.confirm_appointment, name='confirm_appointment'),
    path('staff/', views.staff_appointments, name='staff_appointments'),

    path('confirmed/', views.show_confirmed_appointments, name='confirmed_appointments'),
    path('<int:pk>/checkin/', views.checkin_patient, name='checkin_patient'),



    # path('book/<int:doctor_id>/', views.book_appointment, name='book_appointment_from_DoctorList'),
    path('doctors/', views.doctor_list_view, name='doctor_list'),
    path('appointments/completed/', views.completed_appointments, name='completed_appointments'),
    path('doctors/book/<int:doctor_id>/', views.book_appointment_from_DoctorList, name='book_appointment_from_DoctorList')
]
