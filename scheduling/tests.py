from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import time, timedelta
from accounts.models import User
from appointments.models import Appointment
from .models import DoctorSchedule, ScheduleException
from .forms import DoctorScheduleForm, ScheduleExceptionForm
from .services import generate_daily_slots

class SchedulePermissionTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.patient = User.objects.create_user(
            username='patient1', password='test123', role='PATIENT',
            email='patient1@test.com'
        )
        self.receptionist = User.objects.create_user(
            username='recep1', password='test123', role='RECEPTIONIST',
            email='recep1@test.com'
        )

    def test_patient_cannot_access_schedule_list(self):
        self.client.login(username='patient1', password='test123')
        response = self.client.get(reverse('schedule_list'))
        self.assertEqual(response.status_code, 302)

    def test_receptionist_can_access_schedule_list(self):
        self.client.login(username='recep1', password='test123')
        response = self.client.get(reverse('schedule_list'))
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_redirected(self):
        response = self.client.get(reverse('schedule_list'))
        self.assertEqual(response.status_code, 302)


class DoctorScheduleFormTests(TestCase):

    def setUp(self):
        self.doctor = User.objects.create_user(
            username='doctor1', password='test123', role='DOCTOR',
            email='doctor1@test.com'
        )

    def test_start_time_after_end_time_rejected(self):
        form = DoctorScheduleForm(data={
            'doctor': self.doctor.pk,
            'day_of_week': 0,
            'start_time': '17:00',
            'end_time': '09:00',
            'slot_duration': 30,
            'buffer_time': 5,
        })
        self.assertFalse(form.is_valid())

    def test_valid_schedule_accepted(self):
        form = DoctorScheduleForm(data={
            'doctor': self.doctor.pk,
            'day_of_week': 0,
            'start_time': '09:00',
            'end_time': '17:00',
            'slot_duration': 30,
            'buffer_time': 5,
        })
        self.assertTrue(form.is_valid())

    def test_overlapping_schedule_rejected(self):
        DoctorSchedule.objects.create(
            doctor=self.doctor, day_of_week=1,
            start_time=time(9, 0), end_time=time(17, 0),
            slot_duration=30, buffer_time=5,
        )
        form = DoctorScheduleForm(data={
            'doctor': self.doctor.pk,
            'day_of_week': 1,
            'start_time': '10:00',
            'end_time': '15:00',
            'slot_duration': 30,
            'buffer_time': 5,
        })
        self.assertFalse(form.is_valid())


class ScheduleExceptionFormTests(TestCase):

    def setUp(self):
        self.doctor = User.objects.create_user(
            username='doctor1', password='test123', role='DOCTOR',
            email='doctor1@test.com'
        )

    def test_past_date_rejected(self):
        past = timezone.now().date() - timedelta(days=5)
        form = ScheduleExceptionForm(data={
            'doctor': self.doctor.pk,
            'date': past,
            'is_day_off': True,
        })
        self.assertFalse(form.is_valid())

    def test_valid_day_off(self):
        future = timezone.now().date() + timedelta(days=10)
        form = ScheduleExceptionForm(data={
            'doctor': self.doctor.pk,
            'date': future,
            'is_day_off': True,
            'reason': 'Vacation',
        })
        self.assertTrue(form.is_valid())



class SlotGenerationTests(TestCase):

    def setUp(self):
        self.doctor = User.objects.create_user(
            username='doctor1', password='test123', role='DOCTOR',
            email='doctor1@test.com'
        )

    def _next_weekday(self, weekday):
        today = timezone.now().date()
        days_ahead = weekday - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return today + timedelta(days=days_ahead)

    def test_slots_generated_for_scheduled_day(self):
        DoctorSchedule.objects.create(
            doctor=self.doctor, day_of_week=0,
            start_time=time(9, 0), end_time=time(12, 0),
            slot_duration=30, buffer_time=5,
        )
        next_monday = self._next_weekday(0)
        slots = generate_daily_slots(self.doctor, next_monday)
        self.assertTrue(len(slots) > 0)

    def test_no_slots_for_unscheduled_day(self):
        today = timezone.now().date() + timedelta(days=1)
        slots = generate_daily_slots(self.doctor, today)
        self.assertEqual(len(slots), 0)

    def test_day_off_exception_returns_empty(self):
        DoctorSchedule.objects.create(
            doctor=self.doctor, day_of_week=0,
            start_time=time(9, 0), end_time=time(17, 0),
            slot_duration=30, buffer_time=5,
        )
        next_monday = self._next_weekday(0)
        ScheduleException.objects.create(
            doctor=self.doctor, date=next_monday, is_day_off=True,
        )
        slots = generate_daily_slots(self.doctor, next_monday)
        self.assertEqual(len(slots), 0)


class DoctorQueueTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.doctor = User.objects.create_user(
            username='doctor1', password='test123', role='DOCTOR',
            email='doctor1@test.com'
        )
        self.patient = User.objects.create_user(
            username='patient1', password='test123', role='PATIENT',
            email='patient1@test.com'
        )

    def test_doctor_can_access_queue(self):
        self.client.login(username='doctor1', password='test123')
        response = self.client.get(reverse('doctor_queue'))
        self.assertEqual(response.status_code, 200)

    def test_patient_cannot_access_queue(self):
        self.client.login(username='patient1', password='test123')
        response = self.client.get(reverse('doctor_queue'))
        self.assertEqual(response.status_code, 302)

    def test_queue_shows_checked_in_patients(self):
        self.client.login(username='doctor1', password='test123')
        now = timezone.now()
        Appointment.objects.create(
            doctor=self.doctor, patient=self.patient,
            start_datetime=now,
            end_datetime=now + timedelta(minutes=30),
            status='CHECKED_IN',
            checked_in_at=now - timedelta(minutes=10),
        )
        response = self.client.get(reverse('doctor_queue'))
        self.assertEqual(len(response.context['queue_with_wait']), 1)


class ScheduleCRUDViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.receptionist = User.objects.create_user(
            username='recep1', password='test123', role='RECEPTIONIST',
            email='recep1@test.com'
        )
        self.patient = User.objects.create_user(
            username='patient1', password='test123', role='PATIENT',
            email='patient1@test.com'
        )
        self.doctor = User.objects.create_user(
            username='doctor1', password='test123', role='DOCTOR',
            email='doctor1@test.com'
        )

    def test_receptionist_can_create_schedule(self):
        self.client.login(username='recep1', password='test123')
        response = self.client.post(reverse('schedule_create'), {
            'doctor': self.doctor.pk,
            'day_of_week': 0,
            'start_time': '09:00',
            'end_time': '17:00',
            'slot_duration': 30,
            'buffer_time': 5,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(DoctorSchedule.objects.count(), 1)

    def test_receptionist_can_edit_schedule(self):
        schedule = DoctorSchedule.objects.create(
            doctor=self.doctor, day_of_week=0,
            start_time=time(9, 0), end_time=time(17, 0),
            slot_duration=30, buffer_time=5,
        )
        self.client.login(username='recep1', password='test123')
        response = self.client.post(
            reverse('schedule_update', args=[schedule.pk]), {
                'doctor': self.doctor.pk,
                'day_of_week': 0,
                'start_time': '10:00',
                'end_time': '16:00',
                'slot_duration': 30,
                'buffer_time': 10,
            }
        )
        self.assertEqual(response.status_code, 302)
        schedule.refresh_from_db()
        self.assertEqual(schedule.start_time, time(10, 0))

    def test_delete_schedule_with_confirmation(self):
        schedule = DoctorSchedule.objects.create(
            doctor=self.doctor, day_of_week=0,
            start_time=time(9, 0), end_time=time(17, 0),
            slot_duration=30, buffer_time=5,
        )
        self.client.login(username='recep1', password='test123')
        response = self.client.get(
            reverse('schedule_delete', args=[schedule.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('day_names', response.context)
        response = self.client.post(
            reverse('schedule_delete', args=[schedule.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(DoctorSchedule.objects.count(), 0)

    def test_patient_cannot_delete_schedule(self):
        schedule = DoctorSchedule.objects.create(
            doctor=self.doctor, day_of_week=0,
            start_time=time(9, 0), end_time=time(17, 0),
            slot_duration=30, buffer_time=5,
        )
        self.client.login(username='patient1', password='test123')
        response = self.client.post(
            reverse('schedule_delete', args=[schedule.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(DoctorSchedule.objects.count(), 1)

    def test_receptionist_can_create_exception(self):
        self.client.login(username='recep1', password='test123')
        future = timezone.now().date() + timedelta(days=10)
        response = self.client.post(reverse('exception_create'), {
            'doctor': self.doctor.pk,
            'date': future,
            'is_day_off': True,
            'reason': 'Holiday',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ScheduleException.objects.count(), 1)


class ScheduleExceptionViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.receptionist = User.objects.create_user(
            username='recep1', password='test123', role='RECEPTIONIST',
            email='recep1@test.com'
        )
        self.patient = User.objects.create_user(
            username='patient1', password='test123', role='PATIENT',
            email='patient1@test.com'
        )
        self.doctor = User.objects.create_user(
            username='doctor1', password='test123', role='DOCTOR',
            email='doctor1@test.com'
        )

    def test_receptionist_can_access_exception_list(self):
        self.client.login(username='recep1', password='test123')
        response = self.client.get(reverse('exception_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('upcoming_exceptions', response.context)
        self.assertIn('past_exceptions', response.context)
        self.assertIn('today', response.context)

    def test_patient_cannot_access_exception_list(self):
        self.client.login(username='patient1', password='test123')
        response = self.client.get(reverse('exception_list'))
        self.assertEqual(response.status_code, 302)

    def test_receptionist_can_update_exception(self):
        self.client.login(username='recep1', password='test123')
        exception = ScheduleException.objects.create(
            doctor=self.doctor,
            date=timezone.now().date() + timedelta(days=10),
            is_day_off=True, reason='Original',
        )
        new_date = timezone.now().date() + timedelta(days=20)
        response = self.client.post(
            reverse('exception_update', args=[exception.pk]), {
                'doctor': self.doctor.pk,
                'date': new_date,
                'is_day_off': True,
                'reason': 'Updated',
            }
        )
        self.assertEqual(response.status_code, 302)
        exception.refresh_from_db()
        self.assertEqual(exception.reason, 'Updated')

    def test_invalid_exception_update_rerenders_form(self):
        self.client.login(username='recep1', password='test123')
        exception = ScheduleException.objects.create(
            doctor=self.doctor,
            date=timezone.now().date() + timedelta(days=10),
            is_day_off=True,
        )
        response = self.client.post(
            reverse('exception_update', args=[exception.pk]), {
                'doctor': self.doctor.pk,
                'date': timezone.now().date() - timedelta(days=5),
                'is_day_off': True,
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

    def test_delete_exception_with_confirmation(self):
        self.client.login(username='recep1', password='test123')
        exception = ScheduleException.objects.create(
            doctor=self.doctor,
            date=timezone.now().date() + timedelta(days=10),
            is_day_off=True,
        )
        response = self.client.get(
            reverse('exception_delete', args=[exception.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('exception', response.context)
        response = self.client.post(
            reverse('exception_delete', args=[exception.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ScheduleException.objects.count(), 0)

    def test_patient_cannot_delete_exception(self):
        self.client.login(username='patient1', password='test123')
        exception = ScheduleException.objects.create(
            doctor=self.doctor,
            date=timezone.now().date() + timedelta(days=10),
            is_day_off=True,
        )
        response = self.client.post(
            reverse('exception_delete', args=[exception.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ScheduleException.objects.count(), 1)


class AvailableSlotsViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.doctor = User.objects.create_user(
            username='doctor1', password='test123', role='DOCTOR',
            email='doctor1@test.com'
        )

    def _next_weekday(self, weekday):
        today = timezone.now().date()
        days_ahead = weekday - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return today + timedelta(days=days_ahead)

    def test_missing_date_returns_400(self):
        response = self.client.get(reverse('available_slots'), {
            'doctor_id': self.doctor.pk,
        })
        self.assertEqual(response.status_code, 400)

    def test_valid_request_returns_slots(self):
        DoctorSchedule.objects.create(
            doctor=self.doctor, day_of_week=0,
            start_time=time(9, 0), end_time=time(12, 0),
            slot_duration=30, buffer_time=5,
        )
        next_monday = self._next_weekday(0)
        response = self.client.get(reverse('available_slots'), {
            'doctor_id': self.doctor.pk,
            'date': next_monday.strftime('%Y-%m-%d'),
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('slots', data)
        self.assertTrue(len(data['slots']) > 0)
        self.assertIn('start', data['slots'][0])
        self.assertIn('end', data['slots'][0])

    def test_no_schedule_returns_empty_slots(self):
        next_monday = self._next_weekday(0)
        response = self.client.get(reverse('available_slots'), {
            'doctor_id': self.doctor.pk,
            'date': next_monday.strftime('%Y-%m-%d'),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['slots']), 0)