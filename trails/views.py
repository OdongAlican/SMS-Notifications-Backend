# views.py
from rest_framework import viewsets
from .models import AuditTrail
from .serializers import AuditTrailSerializer

class AuditTrailViewSet(viewsets.ModelViewSet):
    print("Lets Get it started")
    try:
        queryset = AuditTrail.objects.all().select_related('user')
        serializer_class = AuditTrailSerializer
    except Exception as e:
        print(f"Exception: {e}")