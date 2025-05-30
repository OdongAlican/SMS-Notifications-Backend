
from django.urls import path, include
from django.contrib import admin
from pride_notify_notice.views import Email, Sms
from users.authentication import (
    CustomTokenObtainPairView, 
    CustomTokenRefreshView, 
    PasswordResetRequestView, 
    ResetTemporaryPasswordApi,
    UnlockUserAccountView,
    DeactivateUserAccountView,
    ActivateUserAccountView
)
from users.forgotPassword import ForgotPasswordRequestApi, ResetPasswordApi

urlpatterns = [
    path('api/v1/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/change-password/', PasswordResetRequestView.as_view(), name='change-password'),
    path('api/v1/reset-temporary-password/', ResetTemporaryPasswordApi.as_view(), name='reset_temporary_password'),
    path('api/v1/unlock-user-account/', UnlockUserAccountView.as_view(), name='unlock-account'),
    path('api/v1/forgot-password/', ForgotPasswordRequestApi.as_view(), name='forgot-password'),
    path('api/v1/reset-password/', ResetPasswordApi.as_view(), name='reset-password'),
    path('api/v1/deactivate-user/', DeactivateUserAccountView.as_view(), name='deactivate-user'),
    path('api/v1/activate-user/', ActivateUserAccountView.as_view(), name='activate-user'),
    path('api/v1/admin/', admin.site.urls),
    path('api/v1/sms/', Sms.as_view()),
    path('api/v1/email/', Email.as_view()),
    path('api/v1/data/', include('users.urls')),
    path('api/v1/trails/', include('trails.urls')),
    path('api/v1/logs/', include('pride_notify_notice.urls'))
]
