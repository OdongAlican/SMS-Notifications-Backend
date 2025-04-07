from rest_framework.permissions import BasePermission
from django.core.exceptions import PermissionDenied

class CustomGroupPermission(BasePermission):
    """
    Custom permission that checks if a user has a specific permission 
    based on the groups they belong to.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        required_permission_codename = self.get_permission_codename(request, view)

        if not required_permission_codename:
            raise PermissionDenied("No permission required or undefined action")
        
        user_groups = request.user.groups.all()

        for group in user_groups:
            if group.permissions.filter(codename=required_permission_codename).exists():
                return True
        
        return False

    def get_permission_codename(self, request, view):
        """
        Map the HTTP method and view action to a permission codename.
        """
        if view.action == 'list' and request.method == 'GET':
            return 'view_group'
        elif view.action == 'create' and request.method == 'POST':
            return 'add_group'
        elif view.action == 'update' and request.method == 'PUT':
            return 'change_group'
        elif view.action == 'destroy' and request.method == 'DELETE':
            return 'delete_group'

        return None