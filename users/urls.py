from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GroupViewSet, PermissionViewSet, AssignRoleToUserApi, UserPermissionApi, AssignPermissionToGroupApi, RemovePermissionFromGroupApi, UpdateGroupNameApi, UserViewSet

router = DefaultRouter()
router.register("groups", GroupViewSet)
router.register("permissions", PermissionViewSet)
router.register("users", UserViewSet)  # Registering UserViewSet

urlpatterns = [
    path('assign-role/', AssignRoleToUserApi.as_view(), name='assign-role'),
    path('user-permissions/<str:username>/', UserPermissionApi.as_view(), name='user-permissions'),
    path('assign-permission/<int:role_id>/<int:permission_id>/', AssignPermissionToGroupApi.as_view(), name='assign-permission'),
    path('remove-permission/<int:role_id>/<int:permission_id>/', RemovePermissionFromGroupApi.as_view(), name='remove-permission'),
    path('update-group-name/<int:group_id>/', UpdateGroupNameApi.as_view(), name='update-group-name'),
    path('authentication/', include(router.urls)),
]
