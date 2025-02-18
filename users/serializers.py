from django.contrib.auth.models import Group, Permission
from rest_framework import serializers

class GroupSerializer(serializers.ModelSerializer):
    """
    Serializer for Group
    """

    class Meta:
        model = Group
        fields = "__all__"  # Serialize all fields of the Group model

class PermissionSerializer(serializers.ModelSerializer):
    """
    Serializer for Permission
    """

    class Meta:
        model = Permission
        fields = "__all__"  # Serialize all fields of the Permission model
