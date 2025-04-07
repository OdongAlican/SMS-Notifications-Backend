from rest_framework.permissions import BasePermission
from django.core.exceptions import PermissionDenied
from django.utils.text import slugify

class CustomGroupPermission(BasePermission):
    """
    Custom permission that checks if a user has a specific permission 
    based on the groups they belong to.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        required_permission_codename = self.get_permission_codename(request, view)
        print(required_permission_codename, "required_permission_codename")

        if not required_permission_codename:
            raise PermissionDenied("No permission required or undefined action")

        user_groups = request.user.groups.all()

        for group in user_groups:
            if group.permissions.filter(codename=required_permission_codename).exists():
                return True

        return False

    def get_permission_codename(self, request, view):
        """
        Map the HTTP method and view action to a permission codename dynamically
        based on the model and action being performed.
        """
        # Dynamically get the model associated with the view
        model = view.queryset.model if hasattr(view, 'queryset') else None

        if model:
            model_name = slugify(model.__name__)  # Get the lowercase version of the model name, e.g., 'group', 'prideuser'

            if view.action == 'list' and request.method == 'GET':
                return f'view_{model_name}'
            elif view.action == 'create' and request.method == 'POST':
                return f'add_{model_name}'
            elif view.action == 'update' and request.method == 'PUT':
                return f'change_{model_name}'
            elif view.action == 'destroy' and request.method == 'DELETE':
                return f'delete_{model_name}'

        return None