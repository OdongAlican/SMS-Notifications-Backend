from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from .models import AuditTrail
from .serializers import AuditTrailSerializer
from rest_framework.permissions import IsAuthenticated
from users.utils import CustomGroupPermission
class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class AuditTrailViewSet(viewsets.ModelViewSet):
    queryset = AuditTrail.objects.all().select_related('user').filter(user__isnull=False)
    serializer_class = AuditTrailSerializer
    permission_classes = [IsAuthenticated, CustomGroupPermission]
    pagination_class = CustomPageNumberPagination
