from celery import shared_task
# from .serializers import SendBirthdaySMSSerializer
from pride_notify_notice.utils import handle_loans_due, handle_birthdays
from .models import SMSLog
import urllib3
from datetime import datetime
import json


def batch_save_responses(response_data):
    response_objects = []
    for response in response_data:

        # Get the actual result from the AsyncResult object
        # response = result.get()  # This will return the actual response dictionary

        response_objects.append(SMSLog(
            account_name=response['account_name'],
            phone_number=response['phone_number'],
            message=response['message'],
            due_date=response['due_date'],
            amount_due=response['amount_due'],
            status=response['status'],
            response_data=response['response_data'],
        ))

    SMSLog.objects.bulk_create(response_objects)


@shared_task
def retrieve_data():
    loan_data = handle_loans_due()

    for loan in loan_data:
        loan['DUE_DT'] = loan['DUE_DT'].strftime('%Y-%m-%d')
        loan['AMT_DUE'] = float(loan['AMT_DUE'])
    
    updated_loan_list = update_List(loan_data)

    response_data = []

    for loan in updated_loan_list:
        response = send_sms_to_api(loan)
        if response:
            response_data.append(response)

    batch_save_responses(response_data)


# @shared_task
# def retrieve_birthday_data():
#     birthday_data = handle_birthdays()
#     print(birthday_data)

#     birthday_message_serializer = SendBirthdaySMSSerializer(data={"birthdays": birthday_data})
#     if birthday_message_serializer.is_valid():
#         birthday_message_serializer.save()
#     else:
#         print(f"Error: {birthday_message_serializer.errors}")


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def send_sms_to_api(self, loan_detail):

    try:
        http = urllib3.PoolManager(cert_reqs='CERT_NONE', assert_hostname=False)

        acct_nm = loan_detail.get('CUST_NM')
        tel_number = loan_detail.get('TEL_NUMBER')
        due_dt_serial = loan_detail.get('DUE_DT')
        amt_due = loan_detail.get('AMT_DUE')

        if isinstance(due_dt_serial, datetime):
            due_dt = due_dt_serial.strftime('%Y-%m-%d')
        else:
            due_dt = due_dt_serial

        formatted_amt_due = "{:,}".format(round(amt_due))
        message = f"Dear {acct_nm}, your loan installment of {formatted_amt_due} UGX is due on {due_dt}. Thank you for banking with us"

        resp = http.request(
            'GET',
            f"https://192.168.0.35/moonLight/SmsReceiver?sender_name=ibank&password=58c38dca-fc46-4018-a471-265cd7d98ab0&recipient_addr={tel_number}&message={message}"
        )

        response_data = {
            'account_name': acct_nm,
            'phone_number': tel_number,
            'message': message,
            'due_date': due_dt,
            'amount_due': amt_due,
            'status': None,
            'response_data': None
        }

        if 'application/json' in resp.headers.get('Content-Type', ''):
            api_response = json.loads(resp.data.decode('utf-8'))
            response_data['status'] = api_response
            response_data['response_data'] = api_response
        else:
            response_data['status'] = "Failed"
            response_data['response_data'] = {"error": "Non-JSON response received", "details": resp.data.decode('utf-8')}

        return response_data

    except Exception as e:
        response_data = {
            'account_name': acct_nm,
            'phone_number': tel_number,
            'message': message,
            'due_date': due_dt,
            'amount_due': amt_due,
            'status': "Failed",
            'response_data': {"error": str(e)}
        }
        return response_data


def update_List(loan_details):
    test_list = loan_details[:10]
    updated_list = []

    for index, acct in enumerate(test_list):
        if index % 2 == 0:
            acct["TEL_NUMBER"] = "780179148"
        elif index % 3 == 0 and index % 2 != 0:
            acct["TEL_NUMBER"] = "704008866"
        else:
            acct["TEL_NUMBER"] = "780179148"

        updated_list.append(acct)
    return updated_list
