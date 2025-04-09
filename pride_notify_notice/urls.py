from django.urls import path
from .views import SMSLogsForMonthView, BirthDaySMSView

urlpatterns = [
    path('loans/', SMSLogsForMonthView.as_view({"get": "getLoansReport"}), name='sms-logs-month'),
    path('birthdays/', BirthDaySMSView.as_view({"get": "getBirthdayReport"}), name='birthdays-sms-logs-month'),
]
