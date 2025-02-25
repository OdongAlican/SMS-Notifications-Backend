
from django.urls import path, include
from django.contrib import admin
from pride_notify_notice.views import Email, Sms, SMSLogsForMonthView
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    path('api/v1/login/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/', admin.site.urls),  # This line includes the Django admin panel
    path('sms/', Sms.as_view()),
    path('email/', Email.as_view()),
    path('sms/logs/', SMSLogsForMonthView.as_view(), name='sms-logs-month'),
    path('api/v1/', include('users.urls'))
]
