from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv
load_dotenv()

class Command(BaseCommand):
    help = 'Fetch Loans Due in 3 days from the Oracle database'

    def handle(self, *args, **kwargs):
        # Access the Oracle database through a custom connection
        try:
            # Generate a key and display it (store it securely)
            # key = Fernet.generate_key()
            # print("Encryption Key:", key.decode())  # Save this key securely
            # self.stdout.write(str(key))


            # Load the encryption key (replace with your stored key)
            encryption_key = os.environ['ENCRYPTION_KEY'].encode()  
            cipher = Fernet(encryption_key)

            # Encrypt the values
            def encrypt_data(data):
                return cipher.encrypt(data.encode()).decode()

            # Replace with your actual database credentials
            db_name = encrypt_data("customer_engagement")
            db_user = encrypt_data("root")
            db_password = encrypt_data("Sunday@0777338787")
            db_host = encrypt_data("localhost")
            db_port = encrypt_data("3306")
            # db_service_name= encrypt_data("cuzin")

            print(f"MYSQL_ENCRYPT_DATABASE_NAME={db_name}")
            print(f"MYSQL_ENCRYPT_DATABASE_USER={db_user}")
            print(f"MYSQL_ENCRYPT_DATABASE_PASSWORD={db_password}")
            print(f"MYSQL_ENCRYPT_DATABASE_HOST={db_host}")
            print(f"MYSQL_ENCRYPT_DATABASE_PORT={db_port}")

            # print(f"ORACLE_DATABASE_NAME={db_name}")
            # print(f"ORACLE_DATABASE_USER={db_user}")
            # print(f"ORACLE_DATABASE_PASSWORD={db_password}")
            # print(f"ORACLE_DATABASE_HOST={db_host}")
            # print(f"ORACLE_DATABASE_PORT={db_port}")
            # print(f"ORACLE_DATABASE_SERVICE_NAME={db_service_name}")

        except OperationalError as e:
            self.stderr.write(f"Error connecting to Oracle: {e}")