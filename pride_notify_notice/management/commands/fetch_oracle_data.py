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

                # Fetch all rows
                rows = cursor.fetchall()

                # Process your rows (you can print or save them)
                for row in rows:
                    self.stdout.write(str(row))

        except OperationalError as e:
            self.stderr.write(f"Error connecting to Oracle: {e}")
