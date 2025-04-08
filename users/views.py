import secrets
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group, Permission
from rest_framework import viewsets, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import GroupSerializer, PermissionSerializer, UserSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from .utils import CustomGroupPermission, CustomGroupPermissionAssignment
from .models import PrideUser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import exceptions
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
import urllib3
from django.template.loader import render_to_string


class GroupViewSet(viewsets.ModelViewSet):
    """
    Model ViewSet for Group
    """
    queryset = Group.objects.all().prefetch_related('permissions')
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated,CustomGroupPermission]
    authentication_classes = [JWTAuthentication]
    http_method_names = ["get", "post", "patch", "delete"]

class PermissionViewSet(viewsets.ModelViewSet):
    """
    Model ViewSet for Permissions
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    http_method_names = ["get", "post"]

class AssignRoleToUserApi(generics.GenericAPIView):
    """
    Assign a role (group) to a user
    """
    permission_classes = [IsAuthenticated, CustomGroupPermission]

    def post(self, request, user_id, role_id):
        try:
            user = PrideUser.objects.get(id=user_id)
            group = Group.objects.get(id=role_id)

            if group in user.groups.all():
                return Response(
                    {"message": f"{user.username} already has the {group.name} role."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

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

            if group not in user.groups.all():
                return Response(
                    {"message": f"{user.username} does not have the {group.name} role."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

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


class AssignPermissionToGroupApi(viewsets.ViewSet):
    """
    Assign a permission to a group by ID
    """
    permission_classes = [IsAuthenticated, CustomGroupPermissionAssignment]

    def get_permissions(self):
        """
        Override get_permissions to pass the model to the permission class.
        """
        permissions = super().get_permissions()

        # Explicitly set the model being worked with
        for permission in permissions:
            if isinstance(permission, CustomGroupPermission):
                permission.model_info = {'group': Group, 'permission': Permission}

        return permissions

    def assignPermission(self, request, role_id, permission_id):
        try:
            group = Group.objects.get(id=role_id)
            permission = Permission.objects.get(id=permission_id)

            if permission in group.permissions.all():
                return Response(
                    {"message": f"Permission {permission.name} is already assigned to group {group.name}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

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
            group = Group.objects.get(id=role_id)
            permission = Permission.objects.get(id=permission_id)

            if permission not in group.permissions.all():
                return Response(
                    {"message": f"Permission {permission.name} is not assigned to group {group.name}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

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

            new_name = request.data.get("new_name")

            if not new_name:
                return Response({"error": "New name is required."}, status=status.HTTP_400_BAD_REQUEST)

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
    permission_classes = [IsAuthenticated, CustomGroupPermission]
    authentication_classes = [JWTAuthentication]
    http_method_names = ['get', 'post', 'put', 'delete']
    
    def get_permissions(self):
        """
        Custom permissions logic for user actions based on group memberships.
        Specifically restrict the 'create' action based on group permissions.
        """
        permissions = super().get_permissions()
        
        if self.action == 'create':
            self.permission_classes = [IsAuthenticated, CustomGroupPermission]
        elif self.action == 'update':
            self.permission_classes = [IsAuthenticated, CustomGroupPermission]
        elif self.action == 'destroy':
            self.permission_classes = [IsAuthenticated, CustomGroupPermission]
        
        return permissions


    def create(self, request, *args, **kwargs):
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

            if not self.send_email_update_notification(user, password):
                return Response({"error": "User created, but email could not be sent."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                "message": "User created successfully and email sent.",
                "username": user.username,
                "email": user.email,
            }, status=status.HTTP_201_CREATED)

        except KeyError as key_err:
            return Response({"error": f"Missing field: {str(key_err)}"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def update(self, request, user_id=None):
        """
        Handle user update with email check and full user data update.
        """
        try:
            user = PrideUser.objects.get(id=user_id)

            new_email = request.data.get('email')
            first_name = request.data.get('first_name', user.first_name)
            last_name = request.data.get('last_name', user.last_name)

            if new_email and new_email != user.email:
                password = secrets.token_urlsafe(12)
                hashed_password = make_password(password)

                user.email = new_email
                user.password = hashed_password
                user.save()

                self.send_email_update_notification(user, password)

            user.first_name = first_name
            user.last_name = last_name
            user.save()

            return Response({
                "message": "User details updated successfully.",
                "username": user.username,
                "email": user.email,
            }, status=status.HTTP_200_OK)

        except PrideUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def send_email_update_notification(self, user, password):
        http = urllib3.PoolManager(cert_reqs='CERT_NONE')
        try:
            subject = "Your account has been created"
            context = {
                "first_name": user.first_name,
                "otp": password,
                "link": settings.FRONTEND_URL
            }

            html_content = render_to_string("account_creation.html", context)

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

            return resp.status == 200
        except urllib3.exceptions.HTTPError as http_err:
            return False


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