# views.py
from rest_framework import viewsets
from .models import AuditTrail
from .serializers import AuditTrailSerializer

class AuditTrailViewSet(viewsets.ModelViewSet):
    queryset = AuditTrail.objects.all().select_related('user').filter(user__isnull=False)
    serializer_class = AuditTrailSerializer
