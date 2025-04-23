from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Create Super Admin group with all permissions including custom Permissions'

    def handle(self, *args, **kwargs):

        # Step 1: Define custom permission codenames and names
        custom_permissions = [
            ('assign_permission_to_group', 'Can assign permission to group'),
            ('remove_permission_from_group', 'Can remove permission from group'),
            ('assign_group_to_user', 'Can assign group to user'),
            ('remove_group_from_user', 'Can remove group from user'),
            ('view_loan_reports', 'Can view loan reports'),
            ('view_birthday_reports', 'Can view birthday reports'),
        ]

        # Step 2: Use a generic content type (you can also create a dummy model for them if needed)
        content_type, _ = ContentType.objects.get_or_create(
            app_label='custom', model='globalcustompermission'
        )

        # Step 3: Create custom permissions if they don't exist
        for codename, name in custom_permissions:
            Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=content_type
            )
        
        # Step 4: Exclude unwanted permissions
        # These permissions clash with add_group, change_group, delete_group and view_group in the front end.
        excluded_codenames = [
            'add_groupresult',
            'change_groupresult',
            'delete_groupresult',
            'view_groupresult',
            'add_groupaudittrail',
            'change_groupaudittrail',
            'delete_groupaudittrail',
            'view_groupaudittrail'
        ]


        # Step 5: Get all permissions (default + custom)
        # all_permissions = Permission.objects.all()
        all_permissions = Permission.objects.exclude(codename__in=excluded_codenames)

        # Step 6: Create or update group
        group, created = Group.objects.get_or_create(name='Super Admin')
        group.permissions.set(all_permissions)


        # Step 7: Output result
        if created:
            self.stdout.write(self.style.SUCCESS('Super Admin group created and all permissions assigned.'))
        else:
            self.stdout.write(self.style.SUCCESS('Super Admin group updated with all permissions.'))


