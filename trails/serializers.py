# serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .models import AuditTrail

class AuditTrailSerializer(serializers.ModelSerializer):
    # Using StringRelatedField for easy display of user, but you can extend it if you need more details.
    user = serializers.StringRelatedField()  
    object = serializers.SerializerMethodField()

    class Meta:
        model = AuditTrail
        fields = ['id', 'action', 'model_name', 'object_id', 'field_name', 'old_value', 'new_value', 'user', 'timestamp']

    def get_object(self, obj):
        """
        Dynamically load the object related to object_id, 
        which can be a User or Group.
        """
        print(obj.model_name, "Model Name")
        if obj.model_name == 'PrideUser':  # Assume object_id refers to a User
            return get_user_model().objects.get(id=obj.object_id)
        elif obj.model_name == 'Group':  # Assume object_id refers to a Group
            return Group.objects.get(id=obj.object_id)
        return None  # In case object_id doesn't refer to a User or Group
