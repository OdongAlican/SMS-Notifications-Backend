from celery import shared_task
import urllib3
import json
import time
from datetime import datetime, timedelta
from pride_notify_notice.models import SMSLog
from pride_notify_notice.serializers import SendSMSSerializer
from django.db import connections
from django.db.utils import OperationalError
# from pride_notify_service.utils import handle_loans_due


@shared_task
def send_due_loan_sms():
    # Fetch loans due in 3 days (can be refactored from the command)
    # Sample logic; adapt it to fit your query and model

    # loan_details = fetch_due_loan_details()
    loan_data = handle_loans_due()
    print(list(loan_data))

    # Create the serializer instance
    sms_serializer = SendSMSSerializer(data={"loansdue": loan_data})
    
    # If valid data, save and send SMS
    if sms_serializer.is_valid():
        sms_serializer.save()
    else:
        print(f"Error: {sms_serializer.errors}")

# Function to handle the Oracle database query
def handle_loans_due(*args, **kwargs):

    # Access the Oracle database through a custom connection
    try:
        # Use the 'oracle' connection defined in settings.py
        with connections['oracle'].cursor() as cursor:
            query = """
                SELECT 
                    a.cust_id,
                    cn.cust_nm,
                    c.CONTACT AS TEL_NUMBER,
                    b.DUE_DT,
                    SUM(AMT_UNPAID) AS AMT_DUE
                FROM
                    pridelive.ln_acct_repmnt_event b
                INNER JOIN
                    pridelive.account a
                    ON b.acct_id = a.acct_id
                INNER JOIN
                    pridelive.CUSTOMER_CONTACT_MODE c
                    ON b.acct_id = a.acct_id
                    AND a.CUST_ID = c.CUST_ID
                INNER JOIN
                    pridelive.customer cn
                    ON cn.CUST_ID = a.CUST_ID
                WHERE
                    b.REC_ST IN ('N', 'P')
                    AND a.REC_ST IN ('A', 'B', 'Q', 'N')
                    AND c.PREF_CONTACT_MODE = 'Y'
                    AND AMT_UNPAID > 10000
                    AND b.DUE_DT = (
                        SELECT TO_DATE(display_value, 'dd/MM/yyyy')
                        FROM pridelive.ctrl_parameter
                        WHERE param_cd = 'S02'
                    ) + 3
                GROUP BY
                    b.DUE_DT,
                    cn.cust_nm,
                    c.CONTACT,
                    a.cust_id
                ORDER BY
                    a.cust_id
            """
            cursor.execute(query)

            # Fetch all rows and return them as a list of dictionaries
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            # Convert rows into a list of dictionaries
            result = []

            for row in rows:
                row_dict = dict(zip(columns, row))
                result.append(row_dict)

            # Return the result
            return result

    except OperationalError as e:
        # Handle database connection errors
        print(f"Error connecting to Oracle: {e}")
        return []
        

