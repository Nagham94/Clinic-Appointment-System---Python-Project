# ClinicLife — Clinic Appointment System

A full-stack Django clinic management system supporting multi-role workflows for patients, doctors, receptionists, and admins. Built with Django 5.2, PostgreSQL, and a custom dark-themed UI.

---


## User Roles

| Role | Permissions |
|---|---|
| **Patient** | Book, reschedule, cancel, view own appointments and medical records |
| **Doctor** | View daily queue, start consultations, manage EMR, mark no-shows |
| **Receptionist** | Confirm, check in, reschedule, mark no-shows across all appointments |
| **Admin** | Full access + CSV export |

---

## Project Structure

```
clinic_system/
│
├── accounts/           # Custom user model, roles, decorators, auth views
├── scheduling/         # Doctor weekly schedules, slot generator, exceptions
├── appointments/       # Booking, lifecycle management, queue, staff views
├── medical/            # EMR — consultations, prescriptions, requested tests
├── dashboard/          # Role-based dashboards and analytics
│
├── clinic_system/
│   ├── settings.py
│   └── urls.py
│
├── templates/
│   ├── base.html
│   ├── accounts/
│   ├── appointments/
│   ├── scheduling/
│   └── medical/
│
└── static/
    ├── css/
    │   ├── base.css
    │   └── style.css
    └── js/
```

---


## Implementation Phases

### Phase 1 — Authentication & Roles
- Custom user model with role field
- Login, register, logout
- Role-based redirect after login (`dashboard_redirect`)

### Phase 2 — Scheduling
- Doctor weekly schedule model
- Schedule exceptions (holidays, days off)

### Phase 3 — Booking Logic
- Available slots API endpoint
- Double-booking prevention per doctor
- Overlapping appointment prevention per patient
- Past slot filtering for same-day bookings

### Phase 4 — Appointment Lifecycle
- Full status transition engine
- Confirm, check-in, no-show, cancel, delete views


### Phase 5 — EMR (Electronic Medical Records)
- Consultation form with inline prescriptions and requested tests
- Consultation detail with role-based note visibility
- View record linked from queue and appointment history

### Phase 6 — Rescheduling & Audit
- Reschedule by patient or receptionist
- `RescheduleRequest` model stores old/new times, who changed it, and reason
- Status reset to `REQUESTED` after reschedule for re-approval

### Phase 7 — Dashboards & Export
- Patient dashboard with upcoming appointments and quick actions
- Doctor daily queue with wait time badges and status filters
- Receptionist queue manager with confirm/check-in/no-show actions
- Admin CSV export of all appointments

---

## Setup

```bash
git clone https://github.com/your-repo/clinic-appointment-system.git
cd clinic-appointment-system

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Configure your PostgreSQL database in settings.py
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## Environment Variables

Create a `.env` file or configure `settings.py` directly:

```
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/clinic_db
```