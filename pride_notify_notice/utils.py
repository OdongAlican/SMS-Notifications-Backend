from django.db import connections
from django.db.utils import OperationalError
from .models import SMSLog, BirthdaySMSLog

def handle_loans_due(*args, **kwargs):
        try:
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
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                result = []

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    result.append(row_dict)
                return result
        except OperationalError as e:
            print(f"Error connecting to Oracle: {e}")
            return []


def handle_birthdays():
        try:
            with connections['oracle'].cursor() as cursor:
                query = """
                    SELECT * FROM PRIDELIVE.BIRTH_DAY
                """

                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                result = []

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    result.append(row_dict)
                return result
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

    for index, acct in enumerate(test_list):
        if index % 2 == 0:
            acct["TEL_NUMBER"] = "777338787"
        elif index % 3 == 0 and index % 2 != 0:
            acct["TEL_NUMBER"] = "777338787"
        else:
            acct["TEL_NUMBER"] = "777338787"

        updated_list.append(acct)
    return updated_list
