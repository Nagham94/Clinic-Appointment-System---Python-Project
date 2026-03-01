from django.http import JsonResponse
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from datetime import datetime

from django.contrib.auth import get_user_model
from .models import DoctorSchedule, ScheduleException
from .forms import DoctorScheduleForm, ScheduleExceptionForm
from .services import generate_daily_slots

User = get_user_model()

"""
Permission for Receptionist and Admin only
"""
class ScheduleStaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = 'login'
    def test_func(self):
        return (
            self.request.user.is_superuser
            or self.request.user.role in ['RECEPTIONIST', 'ADMIN']
        )

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to manage schedules.")
        return redirect('dashboard_redirect')



"""
Doctor schedule CRUD operations
"""
class DoctorScheduleListView(ScheduleStaffRequiredMixin, ListView):
    model = DoctorSchedule
    template_name = 'scheduling/schedule_list.html'
    context_object_name = 'schedules'
    ordering = ['doctor', 'day_of_week']

    DAY_NAMES = {
        0: 'Monday', 1: 'Tuesday', 2: 'Wednesday',
        3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['day_names'] = self.DAY_NAMES
        return context


class DoctorScheduleCreateView(ScheduleStaffRequiredMixin, CreateView):
    model = DoctorSchedule
    form_class = DoctorScheduleForm
    template_name = 'scheduling/schedule_form.html'
    success_url = reverse_lazy('schedule_list')

    def form_valid(self, form):
        messages.success(self.request, "Schedule created successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class DoctorScheduleUpdateView(ScheduleStaffRequiredMixin, UpdateView):
    model = DoctorSchedule
    form_class = DoctorScheduleForm
    template_name = 'scheduling/schedule_form.html'
    success_url = reverse_lazy('schedule_list')

    def form_valid(self, form):
        messages.success(self.request, "Schedule updated successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class DoctorScheduleDeleteView(ScheduleStaffRequiredMixin, DeleteView):
    model = DoctorSchedule
    template_name = 'scheduling/schedule_confirm_delete.html'
    success_url = reverse_lazy('schedule_list')
    context_object_name = 'schedule'

    DAY_NAMES = {
        0: 'Monday', 1: 'Tuesday', 2: 'Wednesday',
        3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['day_names'] = self.DAY_NAMES
        return context

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Schedule deleted successfully.")
        return super().delete(request, *args, **kwargs)



"""
Doctor schedule exception CRUD operations
"""

class ScheduleExceptionListView(ScheduleStaffRequiredMixin, ListView):
    model = ScheduleException
    template_name = 'scheduling/exception_list.html'
    context_object_name = 'exceptions'
    ordering = ['-date']


class ScheduleExceptionCreateView(ScheduleStaffRequiredMixin, CreateView):
    model = ScheduleException
    form_class = ScheduleExceptionForm
    template_name = 'scheduling/exception_form.html'
    success_url = reverse_lazy('exception_list')

    def form_valid(self, form):
        messages.success(self.request, "Schedule exception created successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class ScheduleExceptionUpdateView(ScheduleStaffRequiredMixin, UpdateView):
    model = ScheduleException
    form_class = ScheduleExceptionForm
    template_name = 'scheduling/exception_form.html'
    success_url = reverse_lazy('exception_list')

    def form_valid(self, form):
        messages.success(self.request, "Schedule exception updated successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class ScheduleExceptionDeleteView(ScheduleStaffRequiredMixin, DeleteView):
    model = ScheduleException
    template_name = 'scheduling/exception_confirm_delete.html'
    success_url = reverse_lazy('exception_list')
    context_object_name = 'exception'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Schedule exception deleted successfully.")
        return super().delete(request, *args, **kwargs)


class AvailableSlotsView(View):
    def get(self, request):
        doctor_id = request.GET.get("doctor_id")
        date_str = request.GET.get("date")

        if not doctor_id or not date_str:
            return JsonResponse({"error": "doctor_id and date are required"}, status=400)

        doctor = User.objects.get(id=doctor_id)
        date = datetime.strptime(date_str, "%Y-%m-%d").date()

        slots = generate_daily_slots(doctor, date)
        formatted_slots = [
            {"start": s[0].strftime("%Y-%m-%d %H:%M"), "end": s[1].strftime("%Y-%m-%d %H:%M")}
            for s in slots
        ]

        return JsonResponse({"slots": formatted_slots})