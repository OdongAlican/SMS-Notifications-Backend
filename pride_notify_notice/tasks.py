from celery import shared_task
from pride_notify_notice.utils import handle_loans_due, handle_birthdays, update_List, update_List_birthdays
import urllib3
from datetime import datetime
import json
from .models import SMSLog, BirthdaySMSLog
import os
from dotenv import load_dotenv
load_dotenv()

@shared_task
def retrieve_data():
    loan_data = handle_loans_due()
    print("Loan Data: ", loan_data)
    # for loan in loan_data:
    #     loan['DUE_DT'] = loan['DUE_DT'].strftime('%Y-%m-%d')
    #     loan['AMT_DUE'] = float(loan['AMT_DUE'])

    # updated_loan_list = update_List(loan_data)

    # response_data = []

    # for loan in updated_loan_list:
    #     response = send_sms_to_api(loan)
    #     if response:
    #         response_data.append(response)


@shared_task
def retrieve_birthday_data():
    birthday_data = handle_birthdays()
    print("Birth day data: ", birthday_data)
    # updated_birthday_list = update_List_birthdays(birthday_data)

    # response_data = []

    # for birthday in updated_birthday_list:
    #     response = send_sms_to_api(birthday)
    #     if response:
    #         response_data.append(response)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def send_sms_to_api(self, message_detail):
    resp = ""
    try:
        http = urllib3.PoolManager(cert_reqs='CERT_NONE', assert_hostname=False)

        if 'AMT_DUE' in message_detail:
            acct_nm = message_detail.get('CUST_NM')
            tel_number = message_detail.get('TEL_NUMBER')
            due_dt_serial = message_detail.get('DUE_DT')
            amt_due = message_detail.get('AMT_DUE')

            if isinstance(due_dt_serial, datetime):
                # due_dt = due_dt_serial.strftime('%Y-%m-%d')
                due_dt = due_dt_serial.strftime('%d-%m-%Y')
            else:
                due_dt = due_dt_serial

            formatted_amt_due = "{:,}".format(round(amt_due))
            message = f"Dear {acct_nm}, your loan installment of {formatted_amt_due} UGX is due on {due_dt}. Thank you for banking with us. Toll Free: 0800333999"
            log_model = SMSLog

        elif 'DATE_OF_BIRTH' in message_detail:
            acct_nm = message_detail.get('ACCT_NM')
            tel_number = message_detail.get('CONTACT')
            date_of_birth = message_detail.get('DATE_OF_BIRTH')
            client_type = message_detail.get('CLIENT_TYPE')
            
            if isinstance(date_of_birth, datetime):
                date_of_birth = date_of_birth.strftime('%Y-%m-%d')

            name = acct_nm.split()[1]

            message = f"Dear {name}, Pride Wishes you a Happy Birthday. We value our relationship with you. Thank you for choosing Pride. Toll Free: 0800333999"

            log_model = BirthdaySMSLog

        else:
            raise ValueError("Invalid message_detail format: neither 'AMT_DUE' nor 'DATE_OF_BIRTH' found.")
        
        sender_name = os.getenv("MOONLIGHT_SENDER_NAME", "default_sender")
        password = os.getenv("MOONLIGHT_SENDER_PASSWORD", "default_password")
        address =  os.getenv("MOONLIGHT_SENDER_ADDRESS", "default_password")

        resp = http.request(
            'GET',
            f"{address}?sender_name={sender_name}&password={password}&recipient_addr={tel_number}&message={message}"
        )

        response_data = {
            'account_name': acct_nm,
            'phone_number': tel_number,
            'message': message,
            'due_date': due_dt if 'due_dt' in locals() else None,
            'amount_due': amt_due if 'amt_due' in locals() else None,
            'status': None,
            'response_data': None
        }

        try:
            api_response = json.loads(resp.data.decode('utf-8'))
            response_data['status'] = api_response
            response_data['response_data'] = api_response
        except json.decoder.JSONDecodeError:
            response_data['status'] = resp.data.decode('utf-8')
            response_data['response_data'] = {"error": resp.data.decode('utf-8')}
        
        if log_model == SMSLog:
            log_model.objects.create(
                account_name=acct_nm,
                phone_number=tel_number,
                message=message,
                due_date=due_dt if 'due_dt' in locals() else None,
                amount_due=amt_due if 'amt_due' in locals() else None,
                status=response_data['status'],
                response_data=response_data['response_data']
            )
        elif log_model == BirthdaySMSLog:
            log_model.objects.create(
                acct_nm=acct_nm,
                client_type=client_type,
                message=message,
                date_of_birth=date_of_birth if 'date_of_birth' in locals() else None,
                contact=tel_number,
                response_data=response_data['response_data'],
                status=response_data['status']
            )

        return response_data

    except Exception as e:
        response_data = {
            'account_name': acct_nm,
            'phone_number': tel_number,
            'message': message,
            'due_date': due_dt if 'due_dt' in locals() else None,
            'amount_due': amt_due if 'amt_due' in locals() else None,
            'status': json.loads(resp.data.decode('utf-8')) if resp else {"error": "No response received"},
            'response_data': {"error": str(e)}
        }

        if log_model == SMSLog:
            log_model.objects.create(
                account_name=acct_nm,
                phone_number=tel_number,
                message=message,
                due_date=due_dt if 'due_dt' in locals() else None,
                amount_due=amt_due if 'amt_due' in locals() else None,
                status=response_data['status'],
                response_data={"error": str(e)}
            )
        elif log_model == BirthdaySMSLog:
            log_model.objects.create(
                acct_nm=acct_nm,
                client_type='Birthday',
                message=message,
                date_of_birth=date_of_birth if 'date_of_birth' in locals() else None,
                contact=tel_number,
                status=response_data['status'],
                response_data={"error": str(e)}
            )

        return response_data