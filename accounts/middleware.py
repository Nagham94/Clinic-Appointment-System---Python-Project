from django.shortcuts import redirect
from django.urls import reverse

class RoleRestrictionMiddleware:
    """
    Middleware to ensure users only access their respective dashboard areas.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_superuser:
            path = request.path
            role = request.user.role
            
            
            role_paths = {
                'PATIENT': reverse('patient_dashboard'),
                'DOCTOR': reverse('doctor_dashboard'),
                'RECEPTIONIST': reverse('receptionist_dashboard'),
                'ADMIN': reverse('admin_dashboard'),
            }
            
            
            for r, p in role_paths.items():
                if path.startswith(p) and role != r:
                    return redirect('dashboard_redirect')

        response = self.get_response(request)
        return response
