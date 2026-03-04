from django.http import JsonResponse
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from datetime import datetime
from collections import OrderedDict
from collections import OrderedDict
from django.utils import timezone
from appointments.models import Appointment
from django.contrib.auth import get_user_model
from .models import DoctorSchedule, ScheduleException
from .forms import DoctorScheduleForm, ScheduleExceptionForm
from .services import generate_daily_slots

import zoneinfo

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

    DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        schedules = self.get_queryset().select_related('doctor')

        # group schedule by doctor
        grouped = OrderedDict()
        for schedule in schedules:
            if schedule.doctor not in grouped:
                grouped[schedule.doctor] = {}
            day_name = self.DAY_NAMES[schedule.day_of_week]
            grouped[schedule.doctor][day_name] = schedule

        context['grouped_schedules'] = grouped
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exceptions = self.get_queryset().select_related('doctor')
        today = timezone.now().date()

        upcoming = []
        past = []

        for exc in exceptions:
            if exc.date >= today:
                upcoming.append(exc)
            else:
                past.append(exc)

        # sort by nearest
        upcoming.sort(key=lambda e: e.date)
        past.sort(key=lambda e: e.date, reverse=True)

        context['upcoming_exceptions'] = upcoming
        context['past_exceptions'] = past
        context['today'] = today
        return context


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



"""
My schedule view for doctors
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

@login_required
def doctor_weekly_schedule(request):
    if request.user.role != 'DOCTOR':
        return redirect('dashboard_redirect')

    DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    schedules = DoctorSchedule.objects.filter(
        doctor=request.user
    ).order_by('day_of_week')

    # Create weekly structure
    weekly_schedule = OrderedDict()

    for index, day in enumerate(DAY_NAMES):
        weekly_schedule[day] = None

    for schedule in schedules:
        day_name = DAY_NAMES[schedule.day_of_week]
        weekly_schedule[day_name] = schedule

    return render(request, 'scheduling/doctor_weekly_schedule.html', {
        'weekly_schedule': weekly_schedule
    })


# ══════════════════════════════════════════════
#  DOCTOR QUEUE DASHBOARD
# ══════════════════════════════════════════════
"""
Doctor queue checked in patients
"""


class DoctorQueueView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'scheduling/doctor_queue.html'
    context_object_name = 'queue'
    login_url = 'login'

    def dispatch(self, request, *args, **kwargs):
        try:
            tz = zoneinfo.ZoneInfo('Africa/Cairo')
        except (ImportError, zoneinfo.ZoneInfoNotFoundError):
            import pytz
            tz = pytz.timezone('Africa/Cairo')
            
        timezone.activate(tz)
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return (
            self.request.user.is_superuser
            or self.request.user.role == 'DOCTOR'
        )

    def handle_no_permission(self):
        messages.error(self.request, "Only doctors can access the queue dashboard.")
        return redirect('dashboard_redirect')

    def get_queryset(self):
        today = timezone.localtime().date()
        
        return Appointment.objects.filter(
            doctor=self.request.user,
            start_datetime__date=today,
            status='CHECKED_IN',
        ).select_related('patient').order_by('checked_in_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        now = timezone.localtime() 
        today = now.date()
        
        context['now'] = now
        context['today'] = today

        # calculate waiting time
        queue_with_wait = []
        for position, appointment in enumerate(context['queue'], start=1):
            check_in_time = appointment.checked_in_at

            if check_in_time:
                wait_delta = now - check_in_time
                total_minutes = int(wait_delta.total_seconds() // 60)
                hours = total_minutes // 60
                minutes = total_minutes % 60
            else:
                total_minutes = 0
                hours = 0
                minutes = 0

            queue_with_wait.append({
                'position': position,
                'appointment': appointment,
                'check_in_time': check_in_time,
                'wait_minutes': total_minutes,
                'wait_hours': hours,
                'wait_mins': minutes,
            })

        context['queue_with_wait'] = queue_with_wait
        context['total_waiting'] = len(queue_with_wait)

        # today's other appointments
        context['upcoming_confirmed'] = Appointment.objects.filter(
            doctor=self.request.user,
            start_datetime__date=today,
            status='CONFIRMED',
        ).select_related('patient').order_by('start_datetime')

        context['completed_today'] = Appointment.objects.filter(
            doctor=self.request.user,
            start_datetime__date=today,
            status='COMPLETED',
        ).count()

        context['no_show_today'] = Appointment.objects.filter(
            doctor=self.request.user,
            start_datetime__date=today,
            status='NO_SHOW',
        ).count()

        return context