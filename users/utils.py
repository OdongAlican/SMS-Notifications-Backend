from rest_framework.permissions import BasePermission
from django.core.exceptions import PermissionDenied
from django.utils.text import slugify
from .models import TokenHistory
from django.conf import settings
from django.template.loader import render_to_string
import urllib3


class IsTokenValid(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Check if the user is enabled
        if not request.user.enabled:
            raise PermissionDenied("Please enable your account.")
        
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

def send_email_notification(user, password, action):
    http = urllib3.PoolManager(cert_reqs='CERT_NONE')
    
    try:
        # Default subject, can be modified based on action
        if action == 'authentication':
            subject = "Your account has been created"
            context = {
                "first_name": user.first_name,
                "otp": password,  # Assuming 'password' is the OTP or password-like string
                "link": settings.FRONTEND_URL  # Link to frontend or a verification page
            }
            template_name = "account_creation.html"  # Template for authentication
        elif action == 'reset':
            subject = "Password Reset Request"
            context = {
                "first_name": user.first_name,
                "reset_token": password,  # The password parameter is now treated as reset token
                "link": f"{settings.FRONTEND_URL}reset-password?token={password}"  # Reset password link with token
            }
            template_name = "password_reset_email.html"  # Template for password reset
        else:
            return False  # Invalid action

        # Render the appropriate template with context
        html_content = render_to_string(template_name, context)

        # Make the HTTP request to send the email
        resp = http.request(
            'POST',
            f"{settings.API_NOTIFICATIONS}/email/",
            fields={
                'sender_email': settings.SENDER_EMAIL,
                'html_message': html_content,
                'subject': subject,
                'to': user.email,
            }
        )

        # Check if the email was sent successfully
        return resp.status == 200
    except urllib3.exceptions.HTTPError as http_err:
        return False
