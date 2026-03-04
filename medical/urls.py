from django.urls import path
from . import views

urlpatterns = [
    path('consultation/create/<int:appointment_id>/', views.create_consultation, name='create_consultation'),
    path('consultation/<int:consultation_id>/', views.consultation_detail, name='consultation_detail'),
]
