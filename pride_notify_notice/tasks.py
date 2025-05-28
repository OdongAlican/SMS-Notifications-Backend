from celery import shared_task
from pride_notify_notice.utils import handle_loans_due, handle_birthdays, update_List, update_List_birthdays
import urllib3
from datetime import datetime
import json
from .models import SMSLog, BirthdaySMSLog
from dateutil.parser import parse
import os
from dotenv import load_dotenv
load_dotenv()

@shared_task(bind=True, max_retries=5, default_retry_delay=300)
def retrieve_data(self):
    try:
        loan_data = handle_loans_due()
        print(loan_data)
        person_list = loan_data.get("Person", [])

        if not person_list:
            raise ValueError("Empty 'Person' list received.")

        updated_loan_list = update_List(person_list)
        response_data = []

        for loan in updated_loan_list:
            response = send_sms_to_api(loan)
            if response:
                response_data.append(response)

        return response_data

    except (ValueError) as e:
        print(f"Data error: {e}")
        raise self.retry(exc=e)

    except Exception as exc:
        print(f"Unexpected error occurred: {exc}")
        raise self.retry(exc=exc)



@shared_task(bind=True, max_retries=5, default_retry_delay=300)
def retrieve_birthday_data(self):
    try:
        birthday_data = handle_birthdays()
        print(birthday_data)
        person_list = birthday_data.get("Person", [])

        if not person_list:
            raise ValueError("Empty 'Person' list received.")

        updated_birthday_list = update_List_birthdays(person_list)
        response_data = []

        for birthday in updated_birthday_list:
            response = send_sms_to_api(birthday)
            if response:
                response_data.append(response)

        return response_data

    except (ValueError) as e:
        print(f"Data error: {e}")
        raise self.retry(exc=e)

    except Exception as exc:
        print(f"Unexpected error occurred: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def send_sms_to_api(self, message_detail):
    resp = ""
    http = urllib3.PoolManager(cert_reqs='CERT_NONE', assert_hostname=False)
    response_data = {}
    
    try:
        # Set up base fields
        acct_nm = ""
        tel_number = ""
        message = ""
        log_model = None
        due_dt_for_db = None
        amt_due = None
        date_of_birth = None

        if 'AMT_DUE' in message_detail:
            # Loan due message
            acct_nm = message_detail.get('CUST_NM')
            tel_number = message_detail.get('TEL_NUMBER')
            due_dt_serial = message_detail.get('DUE_DT')
            amt_due = float(message_detail.get('AMT_DUE', 0))

            due_dt_obj = parse(due_dt_serial) if isinstance(due_dt_serial, str) else due_dt_serial
            due_dt_for_db = due_dt_obj.date()
            due_dt_for_sms = due_dt_obj.strftime('%d-%m-%Y')

            formatted_amt_due = "{:,}".format(round(amt_due))
            message = (
                f"Dear {acct_nm}, your loan installment of {formatted_amt_due} UGX is due on {due_dt_for_sms}. "
                "Thank you for banking with us. Toll Free: 0800333999"
            )
            log_model = SMSLog

        elif 'BIRTH_DT' in message_detail:
            # Birthday message
            acct_nm = message_detail.get('FIRST_NM')
            tel_number = message_detail.get('TEL_NUMBER')
            date_of_birth_raw = message_detail.get('BIRTH_DT')
            client_type = message_detail.get('CLIENT_TYPE')

            try:
                date_of_birth = parse(date_of_birth_raw).date()
            except Exception as e:
                print(f"Failed to parse BIRTH_DT: {e}")
                date_of_birth = None

            message = (
                f"Dear {acct_nm}, Pride Wishes you a Happy Birthday. We value our relationship with you. "
                "Thank you for choosing Pride. Toll Free: 0800333999"
            )
            log_model = BirthdaySMSLog

        else:
            raise ValueError("Invalid message_detail format: neither 'AMT_DUE' nor 'BIRTH_DT' found.")

        # Send SMS
        sender_name = os.getenv("MOONLIGHT_SENDER_NAME", "default_sender")
        password = os.getenv("MOONLIGHT_SENDER_PASSWORD", "default_password")
        address = os.getenv("MOONLIGHT_SENDER_ADDRESS", "http://example.com/api")

        # resp = http.request(
        #     'GET',
        #     f"{address}?sender_name={sender_name}&password={password}&recipient_addr={tel_number}&message={message}"
        # )

        # Attempt to parse response
        # try:
        #     api_response = json.loads(resp.data.decode('utf-8'))
        # except json.decoder.JSONDecodeError:
        #     api_response = {"raw_response": resp.data.decode('utf-8')}
        api_response= ""

        response_data = {
            'account_name': acct_nm,
            'phone_number': tel_number,
            'message': message,
            'due_date': due_dt_for_db,
            'amount_due': amt_due,
            'status': api_response,
            'response_data': api_response
        }

        print(log_model)
        print(f"Using model: {log_model.__name__}")
        # Save to appropriate model
        if log_model == SMSLog:
            log_model.objects.create(
                account_name=acct_nm,
                phone_number=tel_number,
                message=message,
                due_date=due_dt_for_db,
                amount_due=amt_due,
                status=api_response,
                response_data=api_response
            )
        elif log_model == BirthdaySMSLog:
            print(log_model, "Within Birthday")
            print(f"LOGGING BIRTHDAY: {acct_nm}, {tel_number}, {date_of_birth}, {client_type}")
            log_model.objects.create(
                acct_nm=acct_nm,
                client_type=client_type,
                message=message,
                date_of_birth=date_of_birth,
                contact=tel_number,
                status=api_response,
                response_data=api_response
            )

        return response_data

    except Exception as e:
        error_msg = str(e)
        fallback_response = resp.data.decode('utf-8') if resp else "No response received"
        print(f"Error sending SMS: {error_msg}")

        # Log even failed attempts
        if 'SMSLog' in str(type(log_model)):
            log_model.objects.create(
                account_name=acct_nm,
                phone_number=tel_number,
                message=message,
                due_date=due_dt_for_db,
                amount_due=amt_due,
                status=fallback_response,
                response_data={"error": error_msg}
            )
        elif 'BirthdaySMSLog' in str(type(log_model)):
            log_model.objects.create(
                acct_nm=acct_nm,
                client_type=client_type if 'client_type' in locals() else 'Birthday',
                message=message,
                date_of_birth=date_of_birth,
                contact=tel_number,
                status=fallback_response,
                response_data={"error": error_msg}
            )

        return {
            'account_name': acct_nm,
            'phone_number': tel_number,
            'message': message,
            'due_date': due_dt_for_db,
            'amount_due': amt_due,
            'status': fallback_response,
            'response_data': {"error": error_msg}
        }