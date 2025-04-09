
from django.urls import path, include
from django.contrib import admin
from pride_notify_notice.views import Email, Sms
from users.views import CustomTokenObtainPairView
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    path('api/v1/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/admin/', admin.site.urls),
    path('api/v1/sms/', Sms.as_view()),
    path('api/v1/email/', Email.as_view()),
    path('api/v1/data/', include('users.urls')),
    path('api/v1/trails/', include('trails.urls')),
    path('api/v1/logs/', include('pride_notify_notice.urls'))
]
