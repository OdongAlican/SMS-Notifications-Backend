import secrets
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group, Permission
from rest_framework import viewsets, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import GroupSerializer, PermissionSerializer, UserSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from .utils import CustomGroupPermission
from .models import PrideUser
from pride_notify_notice.serializers import SendEmailSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import exceptions
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
import urllib3
import json
from django.template.loader import render_to_string


class GroupViewSet(viewsets.ModelViewSet):
    """
    Model ViewSet for Group
    """
    queryset = Group.objects.all().prefetch_related('permissions')
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated,CustomGroupPermission]  # Permissions to access group views
    authentication_classes = [JWTAuthentication]  # Token authentication
    http_method_names = ["get", "post", "patch", "delete"]  # Allowed HTTP methods

class PermissionViewSet(viewsets.ModelViewSet):
    """
    Model ViewSet for Permissions
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]  # Permissions to access permission views
    authentication_classes = [JWTAuthentication]
    http_method_names = ["get", "post"]  # Allowed HTTP methods

# Custom view to assign a group (role) to a user
class AssignRoleToUserApi(generics.GenericAPIView):
    """
    Assign a role (group) to a user
    """
    permission_classes = [IsAuthenticated]

    def post(self, request,  user_id, role_id):
        try:
            user = PrideUser.objects.get(id=user_id)
            group = Group.objects.get(id=role_id)
            user.groups.add(group)

            return Response(
                {"message": f"Role {group.name} has been assigned to {user.username}."},
                status=status.HTTP_200_OK,
            )
        except PrideUser.DoesNotExist:
            return Response(
                {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Group.DoesNotExist:
            return Response(
                {"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND
            )
        
class RemoveGroupFromUserApi(generics.GenericAPIView):
    """
    Remove a group (role) from a user
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id, role_id):
        try:
            user = PrideUser.objects.get(id=user_id)
            group = Group.objects.get(id=role_id)

            user.groups.remove(group)

            return Response(
                {"message": f"Role {group.name} has been removed from {user.username}."},
                status=status.HTTP_200_OK,
            )
        except PrideUser.DoesNotExist:
            return Response(
                {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Group.DoesNotExist:
            return Response(
                {"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND
            )


# Custom view to get all permissions for a specific user
class UserPermissionApi(generics.GenericAPIView):
    """
    Get Permissions for a specific user
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        try:
            user = PrideUser.objects.get(username=username)

            # Get all permissions for the user's groups
            permissions = user.get_all_permissions()

            return Response(permissions, status=status.HTTP_200_OK)
        except PrideUser.DoesNotExist:
            return Response(
                {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )


class AssignPermissionToGroupApi(generics.GenericAPIView):
    """
    Assign a permission to a group by ID
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, role_id, permission_id):
        try:
            # Get the group and permission objects by their IDs
            group = Group.objects.get(id=role_id)
            permission = Permission.objects.get(id=permission_id)

            # Add the permission to the group
            group.permissions.add(permission)

            return Response(
                {"message": f"Permission {permission.name} has been added to group {group.name}."},
                status=status.HTTP_200_OK,
            )
        except Group.DoesNotExist:
            return Response(
                {"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Permission.DoesNotExist:
            return Response(
                {"error": "Permission not found."}, status=status.HTTP_404_NOT_FOUND
            )
        

class RemovePermissionFromGroupApi(generics.GenericAPIView):
    """
    Remove a permission from a group by ID
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, role_id, permission_id):
        try:
            # Get the group and permission objects by their IDs
            group = Group.objects.get(id=role_id)
            permission = Permission.objects.get(id=permission_id)

            # Remove the permission from the group
            group.permissions.remove(permission)

            return Response(
                {"message": f"Permission {permission.name} has been removed from group {group.name}."},
                status=status.HTTP_200_OK,
            )
        except Group.DoesNotExist:
            return Response(
                {"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Permission.DoesNotExist:
            return Response(
                {"error": "Permission not found."}, status=status.HTTP_404_NOT_FOUND
            )
        
class UpdateGroupNameApi(generics.GenericAPIView):
    """
    Update only the name of a group, keeping permissions intact.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, group_id):
        try:
            group = Group.objects.get(id=group_id)

            # Get the new name from the request body
            new_name = request.data.get("new_name")

            if not new_name:
                return Response({"error": "New name is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Update the group's name
            group.name = new_name
            group.save()

            return Response(
                {"message": f"Group name has been updated to {new_name}."},
                status=status.HTTP_200_OK,
            )
        except Group.DoesNotExist:
            return Response(
                {"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND
            )



class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing users.
    """
    queryset = PrideUser.objects.all().prefetch_related('groups')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    http_method_names = ['get', 'post', 'patch', 'delete']
    
    def get_permissions(self):
        """
        Custom permissions logic for user actions based on group memberships.
        """
        if self.action in ['create', 'update', 'destroy']:
            self.permission_classes = [IsAuthenticated, CustomGroupPermission]
        return super().get_permissions()


    def create(self, request, *args, **kwargs):
        """
        Create a new user with an auto-generated password.
        """
        try:
            password = secrets.token_urlsafe(12)
            hashed_password = make_password(password)

            username = request.data.get('username')
            email = request.data.get('email')
            first_name = request.data.get('first_name')
            last_name = request.data.get('last_name')

            if not all([username, email, first_name, last_name]):
                return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

            user = PrideUser.objects.create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=hashed_password,
            )

            subject = "Your account has been created"

            context = {
                "first_name": user.first_name,
                "otp": password,
                "link": settings.FRONTEND_URL
            }

            html_content = render_to_string("account_creation.html", context)

            http = urllib3.PoolManager(cert_reqs='CERT_NONE')
            try:
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


                if resp.status != 200:
                    return Response({"error": "User created, but email could not be sent."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                data = json.loads(resp.data.decode('utf-8'))

                return Response({
                    "message": f"User created and {data['message']}",
                    "username": user.username,
                    "email": user.email,
                }, status=status.HTTP_201_CREATED)

            except urllib3.exceptions.HTTPError as http_err:
                return Response({"error": f"Email service error: {str(http_err)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except KeyError as key_err:
            return Response({"error": f"Missing field: {str(key_err)}"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            raise exceptions.AuthenticationFailed("Username and password are required.")

        user = authenticate(username=username, password=password)

        if user is None:
            raise exceptions.AuthenticationFailed("Invalid credentials")

        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        user_data = UserSerializer(user).data

        response_data = {
            "refresh": str(refresh),
            "access": str(access_token),
            "user": user_data
        }

        return Response(response_data)