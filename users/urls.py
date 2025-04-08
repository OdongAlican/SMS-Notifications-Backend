from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GroupViewSet,
    PermissionViewSet,
    AssignGroupToUserApi,
    AssignPermissionToGroupApi,
    RemovePermissionFromGroupApi,
    UserViewSet,
    RemoveGroupFromUserApi,
)

router = DefaultRouter()
router.register("groups", GroupViewSet)
router.register("permissions", PermissionViewSet)
router.register("users", UserViewSet)

urlpatterns = [
    path('assign-role/<int:user_id>/<int:role_id>/', AssignGroupToUserApi.as_view({'post': 'assignGroup'}), name='assign-role'),
    path('remove-role/<int:user_id>/<int:role_id>/', RemoveGroupFromUserApi.as_view({'post': 'removeGroup'}), name='remove-role'),
    path('assign-permission/<int:role_id>/<int:permission_id>/', AssignPermissionToGroupApi.as_view({'post': 'assignPermission'}), name='assign-permission'),
    path('remove-permission/<int:role_id>/<int:permission_id>/', RemovePermissionFromGroupApi.as_view({'post': 'removePermission'}), name='remove-permission'),
    path('authentication/', include(router.urls)),
    path('users/<int:user_id>/', UserViewSet.as_view({'put': 'update'}), name='user-update'),
]
