from django.db.utils import OperationalError
from .models import SMSLog, BirthdaySMSLog
import os
import requests
from requests.auth import HTTPBasicAuth
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import json
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
            if response.status_code == 200:
               return response.json()
            else:
                raise ValueError(f"Failed to retrieve data: {response.status_code}")
        except OperationalError as e:
            print(f"Error connecting to Oracle: {e}")
        return []

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

    phone_numbers = [
        "703286023", "0753615464", "704008866", "703987107", "0777338787",
        "0777338787", "0755619185", "780179148", "0777338787", "703286023"
    ]

    for index, acct in enumerate(test_list):
        acct["TEL_NUMBER"] = phone_numbers[index]
        
        updated_list.append(acct)
    
    return updated_list

def update_group_loans(loan_details):
    test_list = loan_details[:10]
    updated_list = []

    phone_numbers = [
        "0703286023", "0782885298", "0703286023", "0703286023", "0757346350",
        "777338787", "0782885298", "0782885298", "0776694688", "0782885298"
    ]

    for index, acct in enumerate(test_list):
        acct["PHONE"] = phone_numbers[index]
        
        updated_list.append(acct)
    
    return updated_list
