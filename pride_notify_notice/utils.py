from django.db import connections
from django.db.utils import OperationalError


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

                # Process the result (return or print it)
                return result
        except OperationalError as e:
            # Handle database connection errors
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

                # Process the result (return or print it)
                return result
        except OperationalError as e:
            # Handle database connection errors
            print(f"Error connecting to Oracle: {e}")
        return []
