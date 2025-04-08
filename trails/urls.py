# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditTrailViewSet

router = DefaultRouter()
router.register(r'audit-trails', AuditTrailViewSet)

urlpatterns = [
    path('trails/', include(router.urls)),
]