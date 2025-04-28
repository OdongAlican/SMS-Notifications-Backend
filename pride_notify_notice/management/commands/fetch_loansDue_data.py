from django.core.management.base import BaseCommand
from django.db.utils import OperationalError
import os
import requests
from requests.auth import HTTPBasicAuth
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import json
load_dotenv()

class Command(BaseCommand):
    help = 'Fetch Loans Due Data from ESB'

    def handle(self, *args, **kwargs):

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
            response = requests.get(f"{external_api_url}?apiKey={api_key}", auth=HTTPBasicAuth(username, password))
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS(json.dumps(response.json(), indent=2)))
            else:
                error_message = {'error': f'Failed to retrieve data: {response.status_code}'}
                self.stdout.write(self.style.ERROR(json.dumps(error_message, indent=2)))

        except OperationalError as e:
            self.stderr.write(f"Error connecting to Oracle: {e}")
