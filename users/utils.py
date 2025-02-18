from rest_framework.permissions import BasePermission

class CustomGroupPermission(BasePermission):
    """
    Custom permission that checks if a user has a specific permission 
    based on the groups they belong to.
    """

    def has_permission(self, request, view):
        # Dynamically determine the required permission based on HTTP method and view action
        required_permission_codename = self.get_permission_codename(request, view)

        if not required_permission_codename:
            return False  # If no permission codename, deny access

        # Loop through each group the user is a part of
        user_groups = request.user.groups.all()

        for group in user_groups:
            # Check if the group has the required permission
            permissions = group.permissions.all()

            for permission in permissions:
                if permission.codename == required_permission_codename:
                    return True  # If the group has the permission, grant access

        return False  # If no group has the required permission, deny access
    
    def get_permission_codename(self, request, view):
        """
        Map the HTTP method and view action to a permission codename.
        """
        if view.action == 'list':
            if request.method == 'GET':
                return 'view_group'  # Permission for listing groups
        elif view.action == 'create':
            if request.method == 'POST':
                return 'add_group'  # Permission for creating a group
        elif view.action == 'update':
            if request.method == 'PATCH':
                return 'change_group'  # Permission for updating a group
        elif view.action == 'destroy':
            if request.method == 'DELETE':
                return 'delete_group'  # Permission for deleting a group

        return None  # Return None if no matching action/permission is found