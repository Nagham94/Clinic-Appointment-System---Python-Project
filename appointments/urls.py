from django.urls import path
from . import views
# from .views import my_appointments

urlpatterns = [
    path('book/', views.book_appointment, name='book_appointment'),
    ##sh
    path('my-appointments/', views.my_appointments, name='my_appointments')
]
