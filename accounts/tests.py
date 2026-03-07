from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import User, PatientProfile, DoctorProfile, ReceptionistProfile
from .forms import (
    PatientRegistrationForm, AdminUserCreationForm, LoginForm,
    PatientProfileForm, DoctorProfileForm
)

class UserModelTests(TestCase):

    def test_user_str_representation(self):
        user = User.objects.create_user(
            username='doctor1', password='test123',
            role='DOCTOR', email='doc@test.com'
        )
        self.assertEqual(str(user), 'doctor1 (DOCTOR)')

    def test_default_role_is_patient(self):
        user = User.objects.create_user(
            username='newuser', password='test123',
            email='new@test.com'
        )
        self.assertEqual(user.role, 'PATIENT')

    def test_patient_profile_str(self):
        user = User.objects.create_user(
            username='patient1', password='test123',
            role='PATIENT', email='pat@test.com'
        )
        profile, _ = PatientProfile.objects.get_or_create(user=user)
        self.assertEqual(str(profile), 'patient1 Profile')

    def test_doctor_profile_str(self):
        user = User.objects.create_user(
            username='doctor1', password='test123',
            role='DOCTOR', email='doc@test.com'
        )
        profile, _ = DoctorProfile.objects.get_or_create(user=user)
        self.assertEqual(str(profile), 'doctor1 Profile')

    def test_receptionist_profile_str(self):
        user = User.objects.create_user(
            username='recep1', password='test123',
            role='RECEPTIONIST', email='recep@test.com'
        )
        profile, _ = ReceptionistProfile.objects.get_or_create(user=user)
        self.assertEqual(str(profile), 'recep1 Profile')


class PatientRegistrationFormTests(TestCase):

    def test_valid_registration(self):
        form = PatientRegistrationForm(data={
            'username': 'newpatient',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@test.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertTrue(form.is_valid())

    def test_duplicate_email_rejected(self):
        User.objects.create_user(
            username='existing', password='test123',
            email='taken@test.com'
        )
        form = PatientRegistrationForm(data={
            'username': 'newuser',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'taken@test.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_saved_user_has_patient_role(self):
        form = PatientRegistrationForm(data={
            'username': 'newpatient',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@test.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        user = form.save()
        self.assertEqual(user.role, 'PATIENT')

    def test_password_mismatch_rejected(self):
        form = PatientRegistrationForm(data={
            'username': 'newpatient',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@test.com',
            'password1': 'StrongPass123!',
            'password2': 'DifferentPass456!',
        })
        self.assertFalse(form.is_valid())


class PatientProfileFormTests(TestCase):

    def test_valid_egyptian_phone(self):
        form = PatientProfileForm(data={
            'phone': '01012345678',
            'date_of_birth': '1990-01-01',
            'address': 'Cairo',
        })
        self.assertTrue(form.is_valid())

    def test_invalid_phone_rejected(self):
        form = PatientProfileForm(data={
            'phone': '12345',
            'date_of_birth': '1990-01-01',
            'address': 'Cairo',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_future_dob_rejected(self):
        future = timezone.now().date() + timedelta(days=30)
        form = PatientProfileForm(data={
            'phone': '',
            'date_of_birth': future,
            'address': '',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('date_of_birth', form.errors)


class LoginLogoutViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.patient = User.objects.create_user(
            username='patient1', password='test123',
            role='PATIENT', email='pat@test.com'
        )

    def test_get_login_page(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_valid_login_redirects(self):
        response = self.client.post(reverse('login'), {
            'username': 'patient1',
            'password': 'test123',
        })
        self.assertEqual(response.status_code, 302)

    def test_invalid_login_rerenders(self):
        response = self.client.post(reverse('login'), {
            'username': 'patient1',
            'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, 200)

    def test_logout_redirects(self):
        self.client.login(username='patient1', password='test123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)


class DashboardRedirectTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_patient_redirected_to_patient_dashboard(self):
        user = User.objects.create_user(
            username='patient1', password='test123',
            role='PATIENT', email='pat@test.com'
        )
        self.client.login(username='patient1', password='test123')
        response = self.client.get(reverse('dashboard_redirect'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('patient', response.url)

    def test_doctor_redirected_to_doctor_dashboard(self):
        user = User.objects.create_user(
            username='doctor1', password='test123',
            role='DOCTOR', email='doc@test.com'
        )
        self.client.login(username='doctor1', password='test123')
        response = self.client.get(reverse('dashboard_redirect'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('doctor', response.url)

    def test_receptionist_redirected_to_receptionist_dashboard(self):
        user = User.objects.create_user(
            username='recep1', password='test123',
            role='RECEPTIONIST', email='recep@test.com'
        )
        self.client.login(username='recep1', password='test123')
        response = self.client.get(reverse('dashboard_redirect'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('receptionist', response.url)

    def test_admin_redirected_to_admin_dashboard(self):
        user = User.objects.create_user(
            username='admin1', password='test123',
            role='ADMIN', email='admin@test.com'
        )
        self.client.login(username='admin1', password='test123')
        response = self.client.get(reverse('dashboard_redirect'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('admin', response.url)


class DashboardAccessTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.patient = User.objects.create_user(
            username='patient1', password='test123',
            role='PATIENT', email='pat@test.com'
        )
        self.doctor = User.objects.create_user(
            username='doctor1', password='test123',
            role='DOCTOR', email='doc@test.com'
        )
        self.receptionist = User.objects.create_user(
            username='recep1', password='test123',
            role='RECEPTIONIST', email='recep@test.com'
        )
        self.admin = User.objects.create_user(
            username='admin1', password='test123',
            role='ADMIN', email='admin@test.com'
        )

    def test_patient_can_access_patient_dashboard(self):
        self.client.login(username='patient1', password='test123')
        response = self.client.get(reverse('patient_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_doctor_cannot_access_patient_dashboard(self):
        self.client.login(username='doctor1', password='test123')
        response = self.client.get(reverse('patient_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_patient_cannot_access_admin_dashboard(self):
        self.client.login(username='patient1', password='test123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_admin_can_access_admin_dashboard(self):
        self.client.login(username='admin1', password='test123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)


class AdminViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin1', password='test123',
            role='ADMIN', email='admin@test.com'
        )
        self.patient = User.objects.create_user(
            username='patient1', password='test123',
            role='PATIENT', email='pat@test.com'
        )

    def test_admin_can_create_user(self):
        self.client.login(username='admin1', password='test123')
        response = self.client.post(reverse('admin_register'), {
            'username': 'newdoctor',
            'first_name': 'New',
            'last_name': 'Doctor',
            'email': 'newdoc@test.com',
            'role': 'DOCTOR',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newdoctor').exists())

    def test_admin_can_view_user_list(self):
        self.client.login(username='admin1', password='test123')
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('users', response.context)