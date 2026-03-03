from django.urls import path
from . import views
# from .views import my_appointments

urlpatterns = [
    path('book/', views.book_appointment, name='book_appointment'),

    # for doctor id
    #  path('book/<int:doctor_id>/', views.book_appointment, name='book_appointment'),

    path('appointment/<int:pk>/delete/', views.delete_appointment, name='delete_appointment'),
    path('my-appointments/', views.my_appointments, name='my_appointments'),
    path('cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('<int:appointment_id>/reschedule/', views.reschedule_appointment, name='reschedule_appointment'),
    path('appointment/<int:pk>/no-show/', views.mark_no_show, name='mark_no_show'),

    path('appointment/<int:pk>/confirm/', views.confirm_appointment, name='confirm_appointment'),
]
