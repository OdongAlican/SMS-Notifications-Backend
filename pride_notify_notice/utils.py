from django.db.utils import OperationalError
from django.conf import settings
from django.utils import timezone
from .models import SMSLog, BirthdaySMSLog
import os
import requests
from requests.auth import HTTPBasicAuth
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from datetime import datetime, time
from dateutil.parser import parse
load_dotenv()

def handle_loans_due():
        encryption_key = os.getenv("ENCRYPTION_KEY")

        if encryption_key is None:
            raise ValueError("Encryption key not found. Set ENCRYPTION_KEY in your environment variables.")

        cipher = Fernet(encryption_key.encode())

        def decrypt_data(encrypted_value):
            return cipher.decrypt(encrypted_value.encode()).decode()
        
        external_api_url = decrypt_data(os.getenv("LOANS_DUE_ESB_URL"))
        password = decrypt_data(os.getenv("ESB_PASSWORD"))
        username = decrypt_data(os.getenv("ESB_USER"))
        api_key = decrypt_data(os.getenv("API_KEY"))

        try:
            response = requests.get(
                f"{external_api_url}?apiKey={api_key}", 
                auth=HTTPBasicAuth(username, password),
                timeout=20,
                verify=False
                )
            if response.status_code == 200:
                return response.json()
            else:
                raise ValueError(f"Failed to retrieve data: {response.status_code}")
        except OperationalError as e:
            print(f"Error connecting to Oracle: {e}")
            return []


def handle_birthdays():
        encryption_key = os.getenv("ENCRYPTION_KEY")

        if encryption_key is None:
            raise ValueError("Encryption key not found. Set ENCRYPTION_KEY in your environment variables.")

        cipher = Fernet(encryption_key.encode())

        def decrypt_data(encrypted_value):
            return cipher.decrypt(encrypted_value.encode()).decode()
        
        external_api_url = decrypt_data(os.getenv("BIRTHDAY_ESB_URL"))
        password = decrypt_data(os.getenv("ESB_PASSWORD"))
        username = decrypt_data(os.getenv("ESB_USER"))
        api_key = decrypt_data(os.getenv("API_KEY"))

        try:
            response = requests.get(
                f"{external_api_url}?apiKey={api_key}", 
                auth=HTTPBasicAuth(username, password),
                timeout=10,
                verify=False
                )
            if response.status_code == 200:
               return response.json()
            else:
                raise ValueError(f"Failed to retrieve data: {response.status_code}")
        except OperationalError as e:
            print(f"Error connecting to Oracle: {e}")
        return []

def handle_Escrow_notifications():
        encryption_key = os.getenv("ENCRYPTION_KEY")

        if encryption_key is None:
            raise ValueError("Encryption key not found. Set ENCRYPTION_KEY in your environment variables.")

        cipher = Fernet(encryption_key.encode())

        def decrypt_data(encrypted_value):
            return cipher.decrypt(encrypted_value.encode()).decode()

        external_api_url = decrypt_data(os.getenv("ESCROW_NOTIFICATIONS"))
        password = decrypt_data(os.getenv("ESB_PASSWORD"))
        username = decrypt_data(os.getenv("ESB_USER"))
        api_key = decrypt_data(os.getenv("API_KEY"))

        try:
            response = requests.get(
                f"{external_api_url}?apiKey={api_key}", 
                auth=HTTPBasicAuth(username, password),
                timeout=10,
                verify=False  # Disable SSL verification for testing purposes
                )
            response.raise_for_status()
            return response.json()
        except OperationalError as exc:
            raise OperationalError(f"Error connecting to Oracle for escrow notifications: {exc}") from exc
        except requests.RequestException as exc:
            raise ConnectionError(f"Error retrieving escrow notifications: {exc}") from exc
        except ValueError as exc:
            raise ValueError(f"Invalid escrow notifications response: {exc}") from exc


def handle_Escrow_no_transaction_report():
        encryption_key = os.getenv("ENCRYPTION_KEY")

        if encryption_key is None:
            raise ValueError("Encryption key not found. Set ENCRYPTION_KEY in your environment variables.")

        cipher = Fernet(encryption_key.encode())

        def decrypt_data(encrypted_value):
            return cipher.decrypt(encrypted_value.encode()).decode()

        external_api_url = decrypt_data(os.getenv("ESCROW_NO_TXN_NOTIFICATIONS"))
        password = decrypt_data(os.getenv("ESB_PASSWORD"))
        username = decrypt_data(os.getenv("ESB_USER"))
        api_key = decrypt_data(os.getenv("API_KEY"))

        try:
            response = requests.get(
                f"{external_api_url}?apiKey={api_key}",
                auth=HTTPBasicAuth(username, password),
                timeout=10,
                verify=False
            )
            response.raise_for_status()
            return response.json()
        except OperationalError as exc:
            raise OperationalError(f"Error connecting to Oracle for fallback escrow report: {exc}") from exc
        except requests.RequestException as exc:
            raise ConnectionError(f"Error retrieving fallback escrow report: {exc}") from exc
        except ValueError as exc:
            raise ValueError(f"Invalid fallback escrow report response: {exc}") from exc

def handle_URA_reports():
        encryption_key = os.getenv("ENCRYPTION_KEY")

        if encryption_key is None:
            raise ValueError("Encryption key not found. Set ENCRYPTION_KEY in your environment variables.")

        cipher = Fernet(encryption_key.encode())

        def decrypt_data(encrypted_value):
            return cipher.decrypt(encrypted_value.encode()).decode()

        external_api_url = decrypt_data(os.getenv("URA_ESB_URL"))
        password = decrypt_data(os.getenv("ESB_PASSWORD"))
        username = decrypt_data(os.getenv("ESB_USER"))
        api_key = decrypt_data(os.getenv("API_KEY"))

        try:
            response = requests.get(
                f"{external_api_url}?apiKey={api_key}", 
                auth=HTTPBasicAuth(username, password),
                timeout=10,
                verify=False  # Disable SSL verification for testing purposes
                )
            if response.status_code == 200:
               return response.json()
            else:
                raise ValueError(f"Failed to retrieve data: {response.status_code}")
        except OperationalError as e:
            print(f"Error connecting to Oracle: {e}")
        return []

def handle_group_loans():
        encryption_key = os.getenv("ENCRYPTION_KEY")

        if encryption_key is None:
            raise ValueError("Encryption key not found. Set ENCRYPTION_KEY in your environment variables.")

        cipher = Fernet(encryption_key.encode())

        def decrypt_data(encrypted_value):
            return cipher.decrypt(encrypted_value.encode()).decode()

        external_api_url = decrypt_data(os.getenv("GROUP_LOANS_ESB_URL"))
        password = decrypt_data(os.getenv("ESB_PASSWORD"))
        username = decrypt_data(os.getenv("ESB_USER"))
        api_key = decrypt_data(os.getenv("API_KEY"))

        try:
            response = requests.get(
                f"{external_api_url}?apiKey={api_key}", 
                auth=HTTPBasicAuth(username, password),
                timeout=20,
                verify=False  # Disable SSL verification for testing purposes
                )
            if response.status_code == 200:
               return response.json()
            else:
                raise ValueError(f"Failed to retrieve data: {response.status_code}")
        except OperationalError as e:
            print(f"Error connecting to Oracle: {e}")
        return []


def handle_ATM_expiry():
        encryption_key = os.getenv("ENCRYPTION_KEY")

        if encryption_key is None:
            raise ValueError("Encryption key not found. Set ENCRYPTION_KEY in your environment variables.")

        cipher = Fernet(encryption_key.encode())

        def decrypt_data(encrypted_value):
            return cipher.decrypt(encrypted_value.encode()).decode()

        external_api_url = decrypt_data(os.getenv("ATM_EXPIRY_ESB_URL"))
        password = decrypt_data(os.getenv("ESB_PASSWORD"))
        username = decrypt_data(os.getenv("ESB_USER"))
        api_key = decrypt_data(os.getenv("API_KEY"))

        try:
            response = requests.get(
                f"{external_api_url}?apiKey={api_key}", 
                auth=HTTPBasicAuth(username, password),
                timeout=30,
                verify=False  # Disable SSL verification for testing purposes
                )
            if response.status_code == 200:
               return response.json()
            else:
                raise ValueError(f"Failed to retrieve data: {response.status_code}")
        except OperationalError as e:
            print(f"Error connecting to Oracle: {e}")
        return []


def batch_save_responses(response_data):
    response_objects_sms_log = []
    response_objects_request_log = []

    for response in response_data:
        if 'AMT_DUE' in response:
            response_objects_sms_log.append(SMSLog(
                account_name=response['account_name'],
                phone_number=response['phone_number'],
                message=response['message'],
                due_date=response['due_date'],
                amount_due=response['amount_due'],
                status=response['status'],
                response_data=response['response_data'],
            ))
        elif 'DATE_OF_BIRTH' in response:

            """
            Ensure that the 'DATE_OF_BIRTH' is passed correctly in the response
            """
            response_objects_request_log.append(BirthdaySMSLog(
                acct_nm=response['account_name'],
                phone_number=response['phone_number'],
                message=response['message'],
                due_date=response['due_date'],
                amount_due=response['amount_due'],
                date_of_birth=response.get('date_of_birth', None),
                status=response['status'],
                response_data=response['response_data'],
            ))

    if response_objects_sms_log:
        SMSLog.objects.bulk_create(response_objects_sms_log)
    if response_objects_request_log:
        BirthdaySMSLog.objects.bulk_create(response_objects_request_log)

def handle_greg_school_reports():
        encryption_key = os.getenv("ENCRYPTION_KEY")

        if encryption_key is None:
            raise ValueError("Encryption key not found. Set ENCRYPTION_KEY in your environment variables.")

        cipher = Fernet(encryption_key.encode())

        def decrypt_data(encrypted_value):
            return cipher.decrypt(encrypted_value.encode()).decode()
        
        external_api_url = decrypt_data(os.getenv("GREG_SCHOOL_REPORTS_ESB_URL"))
        password = decrypt_data(os.getenv("ESB_PASSWORD"))
        username = decrypt_data(os.getenv("ESB_USER"))
        api_key = decrypt_data(os.getenv("API_KEY"))

        try:
            response = requests.get(
                f"{external_api_url}?apiKey={api_key}", 
                auth=HTTPBasicAuth(username, password),
                timeout=10,
                verify=False
                )
            if response.status_code == 200:
               return response.json()
            else:
                raise ValueError(f"Failed to retrieve data: {response.status_code}")
        except OperationalError as e:
            print(f"Error connecting to Oracle: {e}")
        return []

def update_List(loan_details):
    test_list = loan_details[:10]
    updated_list = []

    phone_numbers = [
        "703286023", "0753615464", "704008866", "703987107", "777338787",
        "777338787", "0755619185", "780179148", "777338787", "703286023"
    ]

    for index, acct in enumerate(test_list):
        acct["TEL_NUMBER"] = phone_numbers[index]
        
        updated_list.append(acct)
    
    return updated_list

def update_List_birthdays(loan_details):
    test_list = loan_details[:10]
    updated_list = []

    phone_numbers = getattr(settings, 'TEST_USERS_CONTACTS', [])

    for index, acct in enumerate(test_list):
        acct["TEL_NUMBER"] = phone_numbers[index]
        
        updated_list.append(acct)
    
    return updated_list

def update_List_greg_school_reports(loan_details):
    test_list = loan_details[:5]
    updated_list = []

    phone_numbers = getattr(settings, 'GREG_SCHOOL_USERS_CONTACTS', [])

    for index, acct in enumerate(test_list):
        acct["TEL_NUMBER"] = phone_numbers[index]
        updated_list.append(acct)
    
    return updated_list

def _parse_transaction_datetime(txn_time_str):
    if not txn_time_str:
        return None

    try:
        txn_datetime = parse(str(txn_time_str))
    except (TypeError, ValueError):
        return None

    current_timezone = timezone.get_current_timezone()
    if timezone.is_aware(txn_datetime):
        return timezone.localtime(txn_datetime, current_timezone)

    return timezone.make_aware(txn_datetime, current_timezone)


def filter_today_transactions(transactions, start_time=None, end_time=None):
    current_timezone = timezone.get_current_timezone()
    today = timezone.localtime().date()
    window_start = timezone.make_aware(
        datetime.combine(today, start_time or time.min),
        current_timezone,
    )
    window_end = timezone.make_aware(
        datetime.combine(today, end_time or time.max),
        current_timezone,
    )
    result = []

    for txn in transactions:
        txn_datetime = _parse_transaction_datetime(txn.get('TXN_TIME'))
        if txn_datetime is None:
            continue

        if window_start <= txn_datetime <= window_end:
            result.append(txn)

    return result

def update_ATM_expiry(loan_details):
    test_list = loan_details[:10]
    updated_list = []

    phone_numbers = getattr(settings, 'TEST_USERS_CONTACTS', [])

    for index, acct in enumerate(test_list):
        acct["MOBILE_CONTACT"] = phone_numbers[index]
        
        updated_list.append(acct)
    
    return updated_list

def update_group_loans(loan_details):
    test_list = loan_details[:10]
    updated_list = []

    phone_numbers = getattr(settings, 'TEST_USERS_CONTACTS', [])

    for index, acct in enumerate(test_list):
        acct["PHONE"] = phone_numbers[index]
        
        updated_list.append(acct)
    
    return updated_list


def parse_schedule_time(value, field_name):
    if value is None:
        return None

    for time_format in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(value, time_format).time()
        except ValueError:
            continue

    raise ValueError(
        f"Invalid {field_name} '{value}'. Use HH:MM or HH:MM:SS format."
    )