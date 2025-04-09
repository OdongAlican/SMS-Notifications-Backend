from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .models import AuditTrail
from users.serializers import UserSerializer, GroupSerializer

class AuditTrailSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    object = serializers.SerializerMethodField()

    class Meta:
        model = AuditTrail
        fields = ['id', 'action', 'model_name', 'object_id', 'field_name', 'old_value', 'new_value', 'user', 'timestamp', 'object']

    def get_object(self, obj):
        """
        Dynamically load the object related to object_id, which can be a User or Group.
        """
        if obj.model_name == 'PrideUser':
            try:
                user_instance = get_user_model().objects.get(id=obj.object_id)
                return UserSerializer(user_instance).data
            except get_user_model().DoesNotExist:
                return None
        elif obj.model_name == 'Group':
            try:
                group_instance = Group.objects.get(id=obj.object_id)
                return GroupSerializer(group_instance).data
            except Group.DoesNotExist:
                return None
        return None
