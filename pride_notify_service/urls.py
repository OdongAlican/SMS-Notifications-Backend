
from django.urls import path
from pride_notify_notice.views import Email, Sms, SMSLogsForMonthView

urlpatterns = [
    path('sms/', Sms.as_view()),
    path('email/', Email.as_view()),
    path('sms/logs/', SMSLogsForMonthView.as_view(), name='sms-logs-month'),
]
