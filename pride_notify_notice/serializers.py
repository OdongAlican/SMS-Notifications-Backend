from decimal import Decimal
from rest_framework import serializers
from django.core.mail import EmailMessage
import urllib3
import json
from rest_framework.response import Response
from pride_notify_service import settings
from urllib.parse import quote as url_quote
import time
from datetime import datetime, timedelta
from pride_notify_notice.models import SMSLog

class SendEmailSerializer(serializers.Serializer):
    sender_email = serializers.EmailField(required=True)
    message = serializers.CharField(required=False)
    html_message = serializers.CharField(required=False)
    subject = serializers.CharField(required=True)
    to = serializers.ListField(
        child=serializers.EmailField(), allow_empty=False
    )
    attachments = serializers.ListField(
        child=serializers.FileField(), allow_empty=True, required=False)
    cc = serializers.ListField(
        child=serializers.EmailField(), allow_empty=True, required=False
    )

    def validate(self, attrs):

        def process_attachmment(att):
            return (att.name, att.read(), att.content_type)

        if attrs.get("attachments"):
            attrs["attachments"] = [process_attachmment(
                attachment) for attachment in attrs.get("attachments")]

        return attrs

    def save(self, *args):
        try:
            email = EmailMessage(
                self.validated_data.get("subject"),
                (self.validated_data.get("message") or self.validated_data.get("html_message")),
                self.validated_data.get("sender_email"),
                self.validated_data.get("to"),
                cc=self.validated_data.get("cc"),
                attachments=self.validated_data.get("attachments")
            )
            if self.validated_data.get("html_message"):
                email.content_subtype = "html"
            email.send()
        except Exception as e:
            # TODO: need to alert this exception...
            raise serializers.ValidationError(
                {"email": str(e)})

class LoanDueSerializer(serializers.Serializer):
    CUST_NM = serializers.CharField(required=True)  # Change ACCT_NM to CUST_NM to match the data
    TEL_NUMBER = serializers.CharField(required=True)
    DUE_DT = serializers.CharField(required=True)  # This will remain a string, formatted in the save method
    AMT_DUE = serializers.FloatField(required=True)

    def validate_DUE_DT(self, value):
        # If the DUE_DT is a datetime object, format it as a string (e.g., 'yyyy-mm-dd')
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d')
        return value

class SendSMSSerializer(serializers.Serializer):
    loansdue = LoanDueSerializer(many=True, required=True)

    def mask_account_number(self, acct_no: str) -> str:
        if len(acct_no) > 5:
            masked_acct_no = '*' * (len(acct_no) - 5) + acct_no[-5:]
        else:
            masked_acct_no = acct_no
        return masked_acct_no

    def excel_serial_to_date(self, serial):
        if not serial:
            return None
        try:
            serial = float(serial)
        except ValueError:
            return None
    
        excel_start_date = datetime(1900, 1, 1)
    
        if serial > 60:
            serial -= 1

        delta = timedelta(days=serial)
        return (excel_start_date + delta).date()
    
    def format_amount_due(self, amt_due: float) -> str:
        rounded_amt_due = round(amt_due)
        formatted_amt_due = "{:,}".format(rounded_amt_due)
        return formatted_amt_due

    def save(self, *args, **kwargs):
        data = self.validated_data
        loan_details = data.get('loansdue')

        response_data = []
        
        # Initialize HTTP client
        http = urllib3.PoolManager(cert_reqs='CERT_NONE', assert_hostname=False)


        # Create a test list with 10 records (slicing first 10 items)
        test_list = loan_details[:10]  # Take the first 10 records

        updated_list = []
                
        for index, acct in enumerate(test_list):
            if index % 2 == 0:
                acct["TEL_NUMBER"] = "0777338787"
            elif index % 3 == 0 and index % 2 != 0:
                # acct["TEL_NUMBER"] = "0780179148"
                acct["TEL_NUMBER"] = "0777338787"
            else:
                # acct["TEL_NUMBER"] = "0782885298"
                acct["TEL_NUMBER"] = "0777338787"

            updated_list.append(acct)

        # for loan_detail in loan_details:
        for loan_detail in updated_list:
            try:
                acct_nm = loan_detail.get('CUST_NM')
                tel_number = loan_detail.get('TEL_NUMBER')
                due_dt_serial = loan_detail.get('DUE_DT')
                amt_due = loan_detail.get('AMT_DUE')

                # Format DUE_DT to string if it's datetime object
                if isinstance(due_dt_serial, datetime):
                    due_dt = due_dt_serial.strftime('%Y-%m-%d')  # Convert datetime to 'yyyy-mm-dd'
                else:
                    due_dt = due_dt_serial  # If it's already in string format, keep it

                if not due_dt:
                    response_data.append({"error": f"Invalid due date for account"})
                    
                    # Log the failure
                    SMSLog.objects.create(
                        account_name=acct_nm,
                        phone_number=tel_number,
                        message=f"Invalid due date for account",
                        due_date=None,
                        amount_due=amt_due,
                        status="Failed",
                        response_data={"error": "Invalid due date for account"}
                    )
                    continue

                # Convert AMT_DUE from Decimal to float if necessary
                if isinstance(amt_due, Decimal):
                    amt_due = float(amt_due)

                formatted_amt_due = self.format_amount_due(amt_due)

                message = f"Dear {acct_nm}, your loan installment of {formatted_amt_due} UGX is due on {due_dt}."

                # Sending the SMS
                resp = http.request(
                    'GET',
                    f"https://192.168.0.35/moonLight/SmsReceiver?sender_name=ibank&password=58c38dca-fc46-4018-a471-265cd7d98ab0&recipient_addr={tel_number}&message={message}"
                )

                if 'application/json' in resp.headers.get('Content-Type', ''):
                    try:
                        api_response = json.loads(resp.data.decode('utf-8'))
                        # Log successful response
                        SMSLog.objects.create(
                            account_name=acct_nm,
                            phone_number=tel_number,
                            message=message,
                            due_date=due_dt,
                            amount_due=amt_due,
                            status=api_response,
                            response_data=api_response
                        )
                        response_data.append(api_response)
                        # response_data.append(json.loads(resp.data.decode('utf-8')))
                    except json.JSONDecodeError:
                        response_data.append({"error": "Invalid JSON response"})
                        SMSLog.objects.create(
                            account_name=acct_nm,
                            phone_number=tel_number,
                            message=message,
                            due_date=due_dt,
                            amount_due=amt_due,
                            status=api_response,
                            response_data={"error": "Invalid JSON response"}
                        )
                else:
                    response= resp.data.decode('utf-8')
                    response_data.append({"error": "Non-JSON response received", "details": response})
                    SMSLog.objects.create(
                        account_name=acct_nm,
                        phone_number=tel_number,
                        message=message,
                        due_date=due_dt,
                        amount_due=amt_due,
                        status=response,
                        response_data={"error": "Non-JSON response received"}
                    )

            except urllib3.exceptions.RequestError as e:
                response_data.append({"error": "Request failed", "details": str(e)})
                SMSLog.objects.create(
                    account_name=acct_nm,
                    phone_number=tel_number,
                    message=message,
                    due_date=due_dt,
                    amount_due=amt_due,
                    status="Failed",
                    response_data={"error": "Request failed", "details": str(e)}
                )

            # Wait for 5 seconds before sending the next message
            time.sleep(5)

        return Response(response_data)
    
class SMSLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSLog
        fields = ['id', 'phone_number', 'account_name', 'status', 'created_at', 'response_data', 'due_date', 'amount_due']