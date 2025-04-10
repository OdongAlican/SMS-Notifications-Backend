
from django.urls import path, include
from django.contrib import admin
from pride_notify_notice.views import Email, Sms
from users.views import CustomTokenObtainPairView, CustomTokenRefreshView, PasswordResetRequestView, ResetTemporaryPasswordApi

urlpatterns = [
    path('api/v1/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/change-password/', PasswordResetRequestView.as_view(), name='change-password'),
    path('api/v1/reset-temporary-password/', ResetTemporaryPasswordApi.as_view(), name='reset_temporary_password'),
    path('api/v1/admin/', admin.site.urls),
    path('api/v1/sms/', Sms.as_view()),
    path('api/v1/email/', Email.as_view()),
    path('api/v1/data/', include('users.urls')),
    path('api/v1/trails/', include('trails.urls')),
    path('api/v1/logs/', include('pride_notify_notice.urls'))
]
