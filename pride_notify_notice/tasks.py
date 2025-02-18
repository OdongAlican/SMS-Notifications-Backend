from celery import shared_task
from .serializers import SendSMSSerializer
from pride_notify_notice.utils import handle_loans_due

@shared_task
def retrieve_data():
    loan_data = handle_loans_due()
    # print(loan_data)
    # Ensure the DUE_DT and AMT_DUE are handled correctly before passing them to the serializer
    for loan in loan_data:
        loan['DUE_DT'] = loan['DUE_DT'].strftime('%Y-%m-%d')  # Convert datetime to string
        loan['AMT_DUE'] = float(loan['AMT_DUE'])  # Convert AMT_DUE to float if it's Decimal
    
    sms_serializer = SendSMSSerializer(data={"loansdue": loan_data})
    if sms_serializer.is_valid():
        sms_serializer.save()
    else:
        print(f"Error: {sms_serializer.errors}")

