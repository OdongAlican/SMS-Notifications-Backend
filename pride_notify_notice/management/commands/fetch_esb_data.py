from django.core.management.base import BaseCommand
from django.db.utils import OperationalError
import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import json
load_dotenv()

class Command(BaseCommand):
    help = 'Fetch Loans Due in 3 days from the Oracle database'

    def handle(self, *args, **kwargs):
        external_api_url = os.getenv("ERB_URL")
        password = os.getenv("PASSWORD")
        username = os.getenv("USER")
        api_key = os.getenv("API_KEY")

        print("We are already here!!")

        try:
            # Make the GET request to the external API with basic auth
            response = requests.get(f"{external_api_url}/?apiKey={api_key}", auth=HTTPBasicAuth(username, password))

            if response.status_code == 200:
                # Instead of returning a JsonResponse, write the JSON response to stdout
                self.stdout.write(self.style.SUCCESS(json.dumps(response.json(), indent=2)))
            else:
                # Output error message if status code is not 200
                error_message = {'error': f'Failed to retrieve data: {response.status_code}'}
                self.stdout.write(self.style.ERROR(json.dumps(error_message, indent=2)))

        except OperationalError as e:
            # If there's an issue with the Oracle DB connection
            self.stderr.write(f"Error connecting to Oracle: {e}")
