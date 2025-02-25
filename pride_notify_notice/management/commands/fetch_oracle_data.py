from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError

class Command(BaseCommand):
    help = 'Fetch Loans Due in 3 days from the Oracle database'

    def handle(self, *args, **kwargs):
        # Access the Oracle database through a custom connection
        try:
            # Use the 'oracle' connection defined in settings.py
            with connections['oracle'].cursor() as cursor:
                # Updated SQL query
                query = """
                    SELECT * FROM PRIDELIVE.BIRTH_DAY
                """

                cursor.execute(query)

                # Fetch all rows
                rows = cursor.fetchall()

                # Process your rows (you can print or save them)
                for row in rows:
                    self.stdout.write(str(row))

        except OperationalError as e:
            self.stderr.write(f"Error connecting to Oracle: {e}")
