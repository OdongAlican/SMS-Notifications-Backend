from django.contrib.auth.models import Group, Permission, User
from rest_framework import viewsets, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import GroupSerializer, PermissionSerializer, UserSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from .utils import CustomGroupPermission

class GroupViewSet(viewsets.ModelViewSet):
    """
    Model ViewSet for Group
    """
    queryset = Group.objects.all()
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

    def post(self, request):
        try:
            user = User.objects.get(username=request.data["username"])
            group = Group.objects.get(name=request.data["group_name"])

            # Assign the group (role) to the user
            user.groups.add(group)

            return Response(
                {"message": f"Role {group.name} has been assigned to {user.username}."},
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
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
            user = User.objects.get(username=username)

            # Get all permissions for the user's groups
            permissions = user.get_all_permissions()

            return Response(permissions, status=status.HTTP_200_OK)
        except User.DoesNotExist:
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
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    http_method_names = ['get', 'post', 'patch', 'delete']  # Allow only these HTTP methods
    
    def get_permissions(self):
        """
        Custom permissions logic for user actions based on group memberships.
        """
        if self.action in ['create', 'update', 'destroy']:
            # For create, update, or destroy actions, only users with 'admin' group can access.
            self.permission_classes = [IsAuthenticated, CustomGroupPermission]
        return super().get_permissions()
