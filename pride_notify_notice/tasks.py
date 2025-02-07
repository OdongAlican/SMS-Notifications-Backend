from celery import shared_task
from .serializers import SendSMSSerializer
from pride_notify_notice.utils import handle_loans_due

@shared_task
def retrieve_data():
    loan_data = handle_loans_due()
    sms_serializer = SendSMSSerializer(data={"loansdue": loan_data})
    if sms_serializer.is_valid():
        sms_serializer.save()
    else:
        print(f"Error: {sms_serializer.errors}")

