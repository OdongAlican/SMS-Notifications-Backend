
from django.urls import path
from pride_notify_notice.views import Email, Sms


urlpatterns = [
    path('sms/', Sms.as_view()),
    path('email/', Email.as_view()),
]
