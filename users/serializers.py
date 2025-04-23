from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from .models import PrideUser

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'content_type']

    class Meta:
        model = Permission
        fields = "__all__"

class GroupSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, required=False)

    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions']


class UserSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, required=False)
    class Meta:
        model = PrideUser
        fields = ['id', 'username', 'email', 'first_name', 
                  'last_name', 'enabled', 'groups', 'password_changed_at', 
                  'password_expiry_days', 'must_change_password', 'locked_until', 'is_deactivated']
