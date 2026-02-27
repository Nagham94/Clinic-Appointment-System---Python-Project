# When a new user is created, automatically create a corresponding profile.
# Also to create Groups for each role and assign users to the appropriate group based on their role.

from django.contrib.auth.models import Group

def create_default_groups(sender, **kwargs):
    roles = ['Doctor', 'Patient', 'Receptionist', 'Admin']
    for role in roles:
        Group.objects.get_or_create(name=role)