import secrets
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group, Permission
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import GroupSerializer, PermissionSerializer, UserSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from .utils import CustomGroupPermission, CustomGroupPermissionAssignment, IsTokenValid, send_email_notification
from .models import PrideUser, TokenHistory, PasswordHistory
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import exceptions
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from trails.models import AuditTrail
from trails.threadlocals import get_current_user
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.exceptions import TokenError
from django.utils import timezone
from rest_framework.views import APIView
from datetime import timedelta


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class GroupViewSet(viewsets.ModelViewSet):
    """
    Model ViewSet for Group
    """
    queryset = Group.objects.all().prefetch_related('permissions')
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated,CustomGroupPermission, IsTokenValid]
    authentication_classes = [JWTAuthentication]
    http_method_names = ["get", "post", "put", "delete"]
    pagination_class = CustomPageNumberPagination

class PermissionViewSet(viewsets.ModelViewSet):
    """
    Model ViewSet for Permissions
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    http_method_names = ["get", "post"]

class AssignGroupToUserApi(viewsets.ViewSet):
    """
    Assign a role (group) to a user
    """
    permission_classes = [IsAuthenticated, CustomGroupPermissionAssignment]

    def assignGroup(self, request, user_id, role_id):
        try:
            user = PrideUser.objects.get(id=user_id)
            group = Group.objects.get(id=role_id)

            if group in user.groups.all():
                return Response(
                    {"message": f"{user.username} already has the {group.name} role."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.groups.add(group)

            current_user = get_current_user()

            AuditTrail.objects.create(
                action='ADD',
                model_name='PrideUser',
                object_id=user.id,
                user=current_user,
                field_name='group',
                old_value=None,
                new_value=group.name,
            )

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
          
class RemoveGroupFromUserApi(viewsets.ViewSet):
    """
    Remove a group (role) from a user
    """
    permission_classes = [IsAuthenticated, CustomGroupPermissionAssignment]

    def removeGroup(self, request, user_id, role_id):
        try:
            user = PrideUser.objects.get(id=user_id)
            group = Group.objects.get(id=role_id)

            if group not in user.groups.all():
                return Response(
                    {"message": f"{user.username} does not have the {group.name} role."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.groups.remove(group)
            
            current_user = get_current_user()

            AuditTrail.objects.create(
                action='REMOVE',
                model_name='PrideUser',
                object_id=user.id,
                user=current_user,
                field_name='group',
                old_value=None,
                new_value=group.name,
            )

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

            current_user = get_current_user()
            AuditTrail.objects.create(
                action='ASSIGN',
                model_name='Group',
                object_id=group.id,
                user=current_user,
                field_name='permission',
                old_value=None,
                new_value=permission.name,
            )

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
        

class RemovePermissionFromGroupApi(viewsets.ViewSet):
    """
    Remove a permission from a group by ID
    """
    permission_classes = [IsAuthenticated, CustomGroupPermissionAssignment]

    def removePermission(self, request, role_id, permission_id):
        try:
            group = Group.objects.get(id=role_id)
            permission = Permission.objects.get(id=permission_id)

            if permission not in group.permissions.all():
                return Response(
                    {"message": f"Permission {permission.name} is not assigned to group {group.name}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            group.permissions.remove(permission)

            current_user = get_current_user()

            AuditTrail.objects.create(
                action='REMOVE',
                model_name='Group',
                object_id=group.id,
                user=current_user,
                field_name='permission',
                old_value=None,
                new_value=permission.name,
            )

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


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing users.
    """
    queryset = PrideUser.objects.all().prefetch_related('groups')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, CustomGroupPermission, IsTokenValid]
    authentication_classes = [JWTAuthentication]
    http_method_names = ['get', 'post', 'put', 'delete']
    pagination_class = CustomPageNumberPagination
    
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

            if not send_email_notification(user, password):
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

                send_email_notification(user, password)

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

        # Deactivate any active tokens for the user to prevent concurrency
        # This ensures only the most recent login will have active tokens
        TokenHistory.objects.filter(user=user, is_active=True).update(is_active=False)

        # Store the new refresh token and access token in the TokenHistory model
        token_history = TokenHistory.objects.create(
            user=user,
            refresh_token=str(refresh),
            access_token=str(access_token),
            is_active=True
        )

        user_data = UserSerializer(user).data

        response_data = {
            "refresh": str(refresh),
            "access": str(access_token),
            "user": user_data,
            "token_history_id": token_history.id,
        }

        return Response(response_data)
    
class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):

        refresh_token = request.data.get('refresh')

        if not refresh_token:
            raise exceptions.AuthenticationFailed("Refresh token is required.")

        try:
            # Decode the refresh token
            refresh = RefreshToken(refresh_token)
            print(f"Decoded refresh token: {refresh}")

            # Extract user_id from token payload
            user_id = refresh['user_id']  # Adjust this if you use a different claim for user identification
            print(f"User ID from refresh token: {user_id}")

            # Get the user object
            user = PrideUser.objects.get(id=user_id)  # Query the user based on the user_id
            print(f"User from database: {user}")

            # Deactivate the old refresh token
            TokenHistory.objects.filter(user=user, refresh_token=refresh_token, is_active=True).update(is_active=False)

            # Create new access token
            access_token = refresh.access_token

            # Store the new token in the TokenHistory
            TokenHistory.objects.create(
                user=user,
                access_token=str(access_token),
                refresh_token=refresh_token,
                is_active=True
            )

            return Response({
                "access": str(access_token),
                "refresh": str(refresh_token),
            })

        except TokenError as e:
            print(f"TokenError: {e}")
            raise exceptions.AuthenticationFailed("Invalid refresh token.")
        except PrideUser.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found.")
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise exceptions.AuthenticationFailed("An error occurred while refreshing the token.")
        
class PasswordResetRequestView(APIView):
    
    def post(self, request):
        """
        Change the password of a user. The user needs to provide their current password
        and the new password.
        """
        try:
            user_id = request.data.get('user_id')
            user = PrideUser.objects.get(id=user_id)
            current_password = request.data.get('current_password')
            new_password = request.data.get('new_password')
                
            if not current_password or not new_password:
                return Response({"error": "Both current and new passwords are required."}, status=status.HTTP_400_BAD_REQUEST)

            # Authenticate user with current password
            if not user.check_password(current_password):
                return Response({"error": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

            # Call the custom change_password method
            user.change_password(new_password)

            return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
            
        except PrideUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ResetTemporaryPasswordApi(APIView):
    """
    API for a super admin to send a new temporary password to a user.
    """
    permission_classes = [IsAuthenticated]  # You can restrict this to super admin group permissions if needed.
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        """
        Reset the temporary password for a user if the current temporary password has expired.
        """
        try:
            # Get the user by ID
            user_id = request.data.get('user_id')
            user = PrideUser.objects.get(id=user_id)

            # Check if the temporary password has expired
            if not user.is_temporary_password_expired():
                return Response(
                    {"message": "Temporary password is still valid."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate a new temporary password
            temp_password = secrets.token_urlsafe(12)
            hashed_password = make_password(temp_password)

            # Update the user with the new temporary password and set expiration to 1 hour from now
            user.password = hashed_password
            # user.temporary_password_expiry = timezone.now() + timedelta(hours=1)
            user.temporary_password_expiry = timezone.now() + timedelta(minutes=5)
            user.save()

            # Send the temporary password to the user via email
            if send_email_notification(user, temp_password):
                return Response(
                    {"message": "New temporary password sent to the user."},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": "User created, but email could not be sent."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except PrideUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)