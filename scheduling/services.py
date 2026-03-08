from datetime import datetime, timedelta
from .models import DoctorSchedule, ScheduleException
from appointments.models import Appointment

"""
slot generation function:
read doctor schedule
check schedule exception
generate slots -> duration + buffer
remove slots that exists in the appointment table -> booked
"""

def generate_daily_slots(doctor, date):

    #check exception -> if the day off (true)
    exception = ScheduleException.objects.filter(
        doctor=doctor,
        date=date
    ).first()

    if exception and exception.is_day_off:
        return []  # if the day off -> no slots

    weekday = date.weekday()  # day -> 0=monday, 6=sunday
    
    # day schedule
    schedule = DoctorSchedule.objects.filter(
        doctor=doctor,
        day_of_week=weekday
    ).first()

    if not schedule:
        return []  # if there is no schedule

    # start and end time
    start_time = exception.override_start_time if exception and exception.override_start_time else schedule.start_time
    end_time = exception.override_end_time if exception and exception.override_end_time else schedule.end_time

    slots = []  # to store slots
    current = datetime.combine(date, start_time)
    end_datetime = datetime.combine(date, end_time)

    while current + timedelta(minutes=schedule.slot_duration) <= end_datetime:

        slot_start = current
        slot_end = current + timedelta(minutes=schedule.slot_duration)
        slots.append((slot_start, slot_end))
        current = slot_end + timedelta(minutes=schedule.buffer_time)

    # remove booked slots
    booked = Appointment.objects.filter(
        doctor=doctor,
        start_datetime__date=date
    ).values_list("start_datetime", "end_datetime")
    # convert to naive(No timezone) for comparison with generated slots 
    booked_naive = {
    (b[0].replace(tzinfo=None), b[1].replace(tzinfo=None))
    for b in booked
    }


    available = [] # store available slots

    for slot in slots:
        if slot not in booked_naive:
            available.append(slot)

    # Filter out past slots if the date is today
    if date == datetime.today().date():
        now = datetime.now()
        filtered = []
        for slot_start, slot_end in available:
            if slot_start > now:
                filtered.append((slot_start, slot_end))
        available = filtered

    return available


