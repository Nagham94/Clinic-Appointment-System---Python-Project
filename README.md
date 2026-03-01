# Clinic-Appointment-System---Python-Project

**Project Structure**
```
**clinic_system/
│
├── accounts/          # Users + Roles
├── scheduling/      # Doctor availability + slots
├── appointments/    # Booking + lifecycle + queue
├── medical/         # EMR (consultation record)
├── dashboard/       # Analytics
│
├── clinic_system/
│   ├── settings.py
│   ├── urls.py
│
└── templates/
└── static/**
```

**Template Structure**
```
templates/
    base.html
    accounts/
    appointments/
    scheduling/
    medical/
```

## Implemenation Phases
**Phase 1 – Authentication + Roles**
- Custom user
- Login/Register
- Role-based redirect

**Phase 2 – Scheduling**

- Doctor weekly schedule
- Slot generator function
- Exceptions

**Phase 3 – Booking Logic**

- Prevent double booking
- Prevent overlapping for patient

**Phase 4 – Appointment Lifecycle**

- Status transitions
- Check-in logic
- Queue view

**Phase 5 – EMR**

- Consultation record form
- Permission protection

**Phase 6 – Rescheduling + Audit**

**Phase 7 – Dashboard + CSV Export**