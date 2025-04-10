from rest_framework.permissions import BasePermission
from django.core.exceptions import PermissionDenied
from django.utils.text import slugify
from .models import TokenHistory


class IsTokenValid(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        authorization = request.headers.get('Authorization')
        if not authorization:
            raise PermissionDenied("No authorization header provided.")
        
        access_token = authorization.split(' ')[1]

        try:
            # Check if the provided access token is valid and active
            active_access_token = TokenHistory.objects.get(
                user=request.user, access_token=access_token, is_active=True)

            refresh_token = active_access_token.refresh_token

            # Check if the provided refresh token is valid and active
            active_refresh_token = TokenHistory.objects.get(
                user=request.user, refresh_token=refresh_token, is_active=True)

            return True  # Both tokens are active

        except TokenHistory.DoesNotExist:
            raise PermissionDenied("Your session has been invalidated. Please log in again.")


class CustomGroupPermission(BasePermission):
    """
    Custom permission that checks if a user has a specific permission 
    based on the groups they belong to.
    """

    def has_permission(self, request, view):
        try:
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
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise PermissionDenied("An unexpected error occurred while checking permissions.")

    def get_permission_codename(self, request, view):
        """
        Map the HTTP method and view action to a permission codename dynamically
        based on the model and action being performed.
        """
        model = view.queryset.model if hasattr(view, 'queryset') else None

        if model:
            model_name = slugify(model.__name__)

            if (view.action == 'list' or view.action == 'retrieve') and request.method == 'GET':
                return f'view_{model_name}'
            elif view.action == 'create' and request.method == 'POST':
                return f'add_{model_name}'
            elif view.action == 'update' and request.method == 'PUT':
                return f'change_{model_name}'
            elif view.action == 'destroy' and request.method == 'DELETE':
                return f'delete_{model_name}'

        return None


class CustomGroupPermissionAssignment(BasePermission):
    """
    Custom permission that checks if a user has a specific permission 
    based on the groups they belong to.
    """

    def has_permission(self, request, view):
        try:
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
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise PermissionDenied("An unexpected error occurred while checking permissions.")

    def get_permission_codename(self, request, view):
        """
        Map the HTTP method and view action to a permission codename dynamically
        based on the model and action being performed.
        """
        print(view.action, request.method)

        if view.action == 'assignPermission' and request.method == 'POST':
            return f'assign_permission_to_group'
        elif view.action == 'removePermission' and request.method == 'POST':
            return f'remove_permission_from_group'
        elif view.action == 'assignGroup' and request.method == 'POST':
            return f'assign_group_to_user'
        elif view.action == 'removeGroup' and request.method == 'POST':
            return f'remove_group_from_user'
        elif view.action == 'getLoansReport' and request.method == 'GET':
            return f'view_loan_reports'
        elif view.action == 'getBirthdayReport' and request.method == 'GET':
            return f'view_birthday_reports'
        return None
