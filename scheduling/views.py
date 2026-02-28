from django.http import JsonResponse
from django.views import View
from datetime import datetime
from django.contrib.auth import get_user_model
from .services import generate_daily_slots

User = get_user_model()

# Create your views here.

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