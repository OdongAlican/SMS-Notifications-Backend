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
from .models import PrideUser
from trails.models import AuditTrail
from trails.threadlocals import get_current_user
from rest_framework.pagination import PageNumberPagination


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
    Assign a role (group) to a user (only one group allowed per user)
    """
    permission_classes = [IsAuthenticated, CustomGroupPermissionAssignment]

    def assignGroup(self, request, user_id, role_id):
        try:
            user = PrideUser.objects.get(id=user_id)
            new_group = Group.objects.get(id=role_id)

            # Check if user already has the group
            if new_group in user.groups.all():
                return Response(
                    {"message": f"{user.username} already has the {new_group.name} role."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            current_user = get_current_user()

            # If user has existing groups, remove them and log audit trail
            old_groups = user.groups.all()
            if old_groups.exists():
                for old_group in old_groups:
                    user.groups.remove(old_group)
                    AuditTrail.objects.create(
                        action='REMOVE',
                        model_name='PrideUser',
                        object_id=user.id,
                        user=current_user,
                        field_name='group',
                        old_value=old_group.name,
                        new_value=None,
                    )

            # Assign new group
            user.groups.add(new_group)
            AuditTrail.objects.create(
                action='ADD',
                model_name='PrideUser',
                object_id=user.id,
                user=current_user,
                field_name='group',
                old_value=None,
                new_value=new_group.name,
            )

            return Response(
                {"message": f"Role {new_group.name} has been assigned to {user.username}."},
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

            if not send_email_notification(user, password, "authentication"):
                return Response({"error": "User created, but email could not be sent."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                "message": "User created successfully and email sent.",
                "username": user.username,
                "email": user.email,
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "enabled": user.enabled,
                "groups": GroupSerializer(user.groups.all(), many=True).data,
            }, status=status.HTTP_201_CREATED)

        except KeyError as key_err:
            return Response({"error": f"Missing field: {str(key_err)}"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def update(self, request, pk=None):
        """
        Handle user update with email check and full user data update.
        """
        try:
            user = PrideUser.objects.get(id=pk)

            new_email = request.data.get('email')
            first_name = request.data.get('first_name', user.first_name)
            last_name = request.data.get('last_name', user.last_name)

            if new_email and new_email != user.email:
                password = secrets.token_urlsafe(12)
                hashed_password = make_password(password)

                user.email = new_email
                user.password = hashed_password
                user.save()

                send_email_notification(user, password, "authentication")

            user.first_name = first_name
            user.last_name = last_name
            user.save()

            return Response({
                "message": "User details updated successfully.",
                "username": user.username,
                "email": user.email,
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "enabled": user.enabled,
                "groups": GroupSerializer(user.groups.all(), many=True).data,
            }, status=status.HTTP_200_OK)

        except PrideUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
