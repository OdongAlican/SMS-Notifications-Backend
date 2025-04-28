
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
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('change-password/', PasswordResetRequestView.as_view(), name='change-password'),
    path('reset-temporary-password/', ResetTemporaryPasswordApi.as_view(), name='reset_temporary_password'),
    path('unlock-user-account/', UnlockUserAccountView.as_view(), name='unlock-account'),
    path('forgot-password/', ForgotPasswordRequestApi.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordApi.as_view(), name='reset-password'),
    path('deactivate-user/', DeactivateUserAccountView.as_view(), name='deactivate-user'),
    path('activate-user/', ActivateUserAccountView.as_view(), name='activate-user'),
    path('admin/', admin.site.urls),
    path('sms/', Sms.as_view()),
    path('email/', Email.as_view()),
    path('data/', include('users.urls')),
    path('trails/', include('trails.urls')),
    path('logs/', include('pride_notify_notice.urls'))
]
