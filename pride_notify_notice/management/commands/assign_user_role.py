from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create Super Admin group with all permissions'

    def handle(self, *args, **kwargs):
        # Get the superuser
        superuser = User.objects.get(username='superadmin')

        # Get the Super Admin group
        super_admin_group = Group.objects.get(name='Super Admin')

        # Assign the Super Admin group to the superuser
        superuser.groups.add(super_admin_group)
