from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, time
from accounts.models import User
from .models import Appointment, RescheduleRequest
from scheduling.models import DoctorSchedule


class AppointmentModelTests(TestCase):

    def setUp(self):
        self.doctor = User.objects.create_user(
            username='doctor1', password='test123',
            role='DOCTOR', email='doc@test.com'
        )
        self.patient = User.objects.create_user(
            username='patient1', password='test123',
            role='PATIENT', email='pat@test.com'
        )

    def test_default_status_is_requested(self):
        now = timezone.now()
        appt = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            start_datetime=now,
            end_datetime=now + timedelta(minutes=30),
        )
        self.assertEqual(appt.status, 'REQUESTED')


class BookAppointmentTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.doctor = User.objects.create_user(
            username='doctor1', password='test123',
            role='DOCTOR', email='doc@test.com'
        )
        self.patient = User.objects.create_user(
            username='patient1', password='test123',
            role='PATIENT', email='pat@test.com'
        )
        DoctorSchedule.objects.create(
            doctor=self.doctor, day_of_week=0,
            start_time=time(9, 0), end_time=time(17, 0),
            slot_duration=30, buffer_time=5,
        )

    def _next_weekday(self, weekday):
        today = timezone.now().date()
        days_ahead = weekday - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return today + timedelta(days=days_ahead)

    def test_get_booking_page(self):
        self.client.login(username='patient1', password='test123')
        response = self.client.get(reverse('book_appointment'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('doctors', response.context)

    def test_unauthenticated_redirected(self):
        response = self.client.get(reverse('book_appointment'))
        self.assertEqual(response.status_code, 302)

    def test_past_slot_rejected(self):
        self.client.login(username='patient1', password='test123')
        past = timezone.now() - timedelta(days=2)
        response = self.client.post(reverse('book_appointment'), {
            'doctor': self.doctor.pk,
            'reason': 'Checkup',
            'start_datetime': past.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': (past + timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M'),
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Appointment.objects.count(), 0)

    def test_booking_creates_appointment(self):
        self.client.login(username='patient1', password='test123')
        next_monday = self._next_weekday(0)
        start = timezone.make_aware(
            timezone.datetime(next_monday.year, next_monday.month, next_monday.day, 9, 0)
        )
        end = start + timedelta(minutes=30)
        response = self.client.post(reverse('book_appointment'), {
            'doctor': self.doctor.pk,
            'reason': 'Checkup',
            'start_datetime': start.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': end.strftime('%Y-%m-%dT%H:%M'),
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Appointment.objects.count(), 1)
        self.assertEqual(Appointment.objects.first().status, 'REQUESTED')


class CancelAppointmentTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.doctor = User.objects.create_user(
            username='doctor1', password='test123',
            role='DOCTOR', email='doc@test.com'
        )
        self.patient = User.objects.create_user(
            username='patient1', password='test123',
            role='PATIENT', email='pat@test.com'
        )
        self.patient2 = User.objects.create_user(
            username='patient2', password='test123',
            role='PATIENT', email='pat2@test.com'
        )
        now = timezone.now() + timedelta(hours=2)
        self.appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            start_datetime=now,
            end_datetime=now + timedelta(minutes=30),
            status='CONFIRMED',
        )

    def test_patient_can_cancel_own_appointment(self):
        self.client.login(username='patient1', password='test123')
        response = self.client.post(
            reverse('cancel_appointment', args=[self.appointment.id])
        )
        self.assertEqual(response.status_code, 302)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'CANCELLED')

    def test_other_patient_cannot_cancel(self):
        self.client.login(username='patient2', password='test123')
        response = self.client.post(
            reverse('cancel_appointment', args=[self.appointment.id])
        )
        self.appointment.refresh_from_db()
        self.assertNotEqual(self.appointment.status, 'CANCELLED')

    def test_cannot_cancel_completed_appointment(self):
        self.appointment.status = 'COMPLETED'
        self.appointment.save()
        self.client.login(username='patient1', password='test123')
        response = self.client.post(
            reverse('cancel_appointment', args=[self.appointment.id])
        )
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'COMPLETED')

    def test_receptionist_can_cancel(self):
        self.client.login(username='doctor1', password='test123')
        response = self.client.post(
            reverse('cancel_appointment', args=[self.appointment.id])
        )
        self.assertEqual(response.status_code, 302)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'CANCELLED')


class ConfirmAppointmentTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.doctor = User.objects.create_user(
            username='doctor1', password='test123',
            role='DOCTOR', email='doc@test.com'
        )
        self.patient = User.objects.create_user(
            username='patient1', password='test123',
            role='PATIENT', email='pat@test.com'
        )
        self.receptionist = User.objects.create_user(
            username='recep1', password='test123',
            role='RECEPTIONIST', email='recep@test.com'
        )
        now = timezone.now() + timedelta(hours=2)
        self.appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            start_datetime=now,
            end_datetime=now + timedelta(minutes=30),
            status='REQUESTED',
        )

    def test_receptionist_can_confirm(self):
        self.client.login(username='recep1', password='test123')
        response = self.client.get(
            reverse('confirm_appointment', args=[self.appointment.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'CONFIRMED')

    def test_patient_cannot_confirm(self):
        self.client.login(username='patient1', password='test123')
        response = self.client.get(
            reverse('confirm_appointment', args=[self.appointment.pk])
        )
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'REQUESTED')


class CheckinTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.doctor = User.objects.create_user(
            username='doctor1', password='test123',
            role='DOCTOR', email='doc@test.com'
        )
        self.patient = User.objects.create_user(
            username='patient1', password='test123',
            role='PATIENT', email='pat@test.com'
        )
        self.receptionist = User.objects.create_user(
            username='recep1', password='test123',
            role='RECEPTIONIST', email='recep@test.com'
        )
        now = timezone.now() + timedelta(hours=1)
        self.appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            start_datetime=now,
            end_datetime=now + timedelta(minutes=30),
            status='CONFIRMED',
        )

    def test_receptionist_can_checkin(self):
        self.client.login(username='recep1', password='test123')
        response = self.client.get(
            reverse('checkin_patient', args=[self.appointment.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'CHECKED_IN')
        self.assertIsNotNone(self.appointment.checked_in_at)

    def test_patient_cannot_checkin(self):
        self.client.login(username='patient1', password='test123')
        response = self.client.get(
            reverse('checkin_patient', args=[self.appointment.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'CONFIRMED')


class MarkNoShowTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.doctor = User.objects.create_user(
            username='doctor1', password='test123',
            role='DOCTOR', email='doc@test.com'
        )
        self.patient = User.objects.create_user(
            username='patient1', password='test123',
            role='PATIENT', email='pat@test.com'
        )
        self.receptionist = User.objects.create_user(
            username='recep1', password='test123',
            role='RECEPTIONIST', email='recep@test.com'
        )
        past = timezone.now() - timedelta(hours=2)
        self.appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            start_datetime=past,
            end_datetime=past + timedelta(minutes=30),
            status='CONFIRMED',
        )

    def test_receptionist_can_mark_no_show(self):
        self.client.login(username='recep1', password='test123')
        response = self.client.get(
            reverse('mark_no_show', args=[self.appointment.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'NO_SHOW')

    def test_cannot_mark_no_show_before_appointment_time(self):
        future = timezone.now() + timedelta(hours=5)
        self.appointment.start_datetime = future
        self.appointment.end_datetime = future + timedelta(minutes=30)
        self.appointment.save()
        self.client.login(username='recep1', password='test123')
        response = self.client.get(
            reverse('mark_no_show', args=[self.appointment.pk])
        )
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'CONFIRMED')


class MyAppointmentsTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.doctor = User.objects.create_user(
            username='doctor1', password='test123',
            role='DOCTOR', email='doc@test.com'
        )
        self.patient = User.objects.create_user(
            username='patient1', password='test123',
            role='PATIENT', email='pat@test.com'
        )

    def test_patient_sees_own_appointments(self):
        self.client.login(username='patient1', password='test123')
        now = timezone.now() + timedelta(hours=1)
        Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            start_datetime=now,
            end_datetime=now + timedelta(minutes=30),
        )
        response = self.client.get(reverse('my_appointments'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['appointments']), 1)

    def test_unauthenticated_redirected(self):
        response = self.client.get(reverse('my_appointments'))
        self.assertEqual(response.status_code, 302)


class StaffAppointmentsTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.doctor = User.objects.create_user(
            username='doctor1', password='test123',
            role='DOCTOR', email='doc@test.com'
        )
        self.patient = User.objects.create_user(
            username='patient1', password='test123',
            role='PATIENT', email='pat@test.com'
        )
        self.receptionist = User.objects.create_user(
            username='recep1', password='test123',
            role='RECEPTIONIST', email='recep@test.com'
        )
        now = timezone.now() + timedelta(hours=1)
        self.appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            start_datetime=now,
            end_datetime=now + timedelta(minutes=30),
            status='CONFIRMED',
        )

    def test_receptionist_can_access(self):
        self.client.login(username='recep1', password='test123')
        response = self.client.get(reverse('staff_appointments'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('appointments', response.context)

    def test_patient_cannot_access(self):
        self.client.login(username='patient1', password='test123')
        response = self.client.get(reverse('staff_appointments'))
        self.assertEqual(response.status_code, 302)

    def test_filter_by_status(self):
        self.client.login(username='recep1', password='test123')
        response = self.client.get(reverse('staff_appointments'), {
            'status': 'CONFIRMED',
        })
        self.assertEqual(response.status_code, 200)
        for appt in response.context['appointments']:
            self.assertEqual(appt.status, 'CONFIRMED')

    def test_search_by_patient_name(self):
        self.client.login(username='recep1', password='test123')
        response = self.client.get(reverse('staff_appointments'), {
            'q': 'patient1',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context['appointments']) >= 1)


class ConfirmedAppointmentsTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.doctor = User.objects.create_user(
            username='doctor1', password='test123',
            role='DOCTOR', email='doc@test.com'
        )
        self.patient = User.objects.create_user(
            username='patient1', password='test123',
            role='PATIENT', email='pat@test.com'
        )
        self.receptionist = User.objects.create_user(
            username='recep1', password='test123',
            role='RECEPTIONIST', email='recep@test.com'
        )
        now = timezone.now() + timedelta(hours=1)
        Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            start_datetime=now,
            end_datetime=now + timedelta(minutes=30),
            status='CONFIRMED',
        )

    def test_receptionist_can_access(self):
        self.client.login(username='recep1', password='test123')
        response = self.client.get(reverse('confirmed_appointments'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('appointments', response.context)

    def test_doctor_sees_only_own(self):
        self.client.login(username='doctor1', password='test123')
        response = self.client.get(reverse('confirmed_appointments'))
        self.assertEqual(response.status_code, 200)
        for appt in response.context['appointments']:
            self.assertEqual(appt.doctor, self.doctor)

    def test_patient_cannot_access(self):
        self.client.login(username='patient1', password='test123')
        response = self.client.get(reverse('confirmed_appointments'))
        self.assertEqual(response.status_code, 302)


class RescheduleAppointmentTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.doctor = User.objects.create_user(
            username='doctor1', password='test123',
            role='DOCTOR', email='doc@test.com'
        )
        self.patient = User.objects.create_user(
            username='patient1', password='test123',
            role='PATIENT', email='pat@test.com'
        )
        self.receptionist = User.objects.create_user(
            username='recep1', password='test123',
            role='RECEPTIONIST', email='recep@test.com'
        )
        DoctorSchedule.objects.create(
            doctor=self.doctor, day_of_week=0,
            start_time=time(9, 0), end_time=time(17, 0),
            slot_duration=30, buffer_time=5,
        )
        now = timezone.now() + timedelta(hours=2)
        self.appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            start_datetime=now,
            end_datetime=now + timedelta(minutes=30),
            status='CONFIRMED',
        )

    def _next_weekday(self, weekday):
        today = timezone.now().date()
        days_ahead = weekday - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return today + timedelta(days=days_ahead)


    def test_cannot_reschedule_completed(self):
        self.appointment.status = 'COMPLETED'
        self.appointment.save()
        self.client.login(username='patient1', password='test123')
        response = self.client.get(
            reverse('reschedule_appointment', args=[self.appointment.id])
        )
        self.assertEqual(response.status_code, 302)

    def test_cannot_reschedule_to_past(self):
        self.client.login(username='patient1', password='test123')
        past = timezone.now() - timedelta(days=2)
        response = self.client.post(
            reverse('reschedule_appointment', args=[self.appointment.id]), {
                'start_datetime': past.strftime('%Y-%m-%dT%H:%M'),
                'end_datetime': (past + timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M'),
                'reason': 'Need earlier time',
            }
        )
        self.assertEqual(response.status_code, 302)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'CONFIRMED')