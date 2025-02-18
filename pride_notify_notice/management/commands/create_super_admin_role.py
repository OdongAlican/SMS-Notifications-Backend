from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Create Super Admin group with all permissions'

    def handle(self, *args, **kwargs):
        # Create a new Super Admin group
        super_admin_group, created = Group.objects.get_or_create(name="Super Admin")
        
        if created:
            # Assign all permissions to this group
            permissions = Permission.objects.all()
            super_admin_group.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS("Super Admin group created and all permissions assigned"))
        else:
            self.stdout.write(self.style.SUCCESS("Super Admin group already exists"))
