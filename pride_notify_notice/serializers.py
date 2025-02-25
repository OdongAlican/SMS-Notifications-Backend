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
from pride_notify_notice.models import SMSLog, RequestDatatLogs, BirthdayRequestsRequestDatatLogs
from .tasks import send_sms_to_api, update_List, batch_save_responses

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
    CUST_NM = serializers.CharField(required=True)
    TEL_NUMBER = serializers.CharField(required=True)
    DUE_DT = serializers.CharField(required=True)
    AMT_DUE = serializers.FloatField(required=True)

    def validate_DUE_DT(self, value):
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d')
        return value

class SendSMSSerializer(serializers.Serializer):
    loansdue = LoanDueSerializer(many=True, required=True)

    def format_amount_due(self, amt_due: float) -> str:
        """Format amount due for SMS message."""
        rounded_amt_due = round(amt_due)
        return "{:,}".format(rounded_amt_due)


    def save(self, *args, **kwargs):
        loan_details = self.validated_data.get('loansdue')
        new_list = update_List(loan_details)

        task_results = []

        for loan in new_list:
            # task_results.append(send_sms_to_api.apply_async(args=[loan]))
            response = send_sms_to_api(loan)
            if response:
                task_results.append(response)

        batch_save_responses(task_results)
        
        return Response(task_results)
    

class SMSLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSLog
        fields = ['id', 'phone_number', 'account_name', 'status', 'created_at', 'response_data', 'due_date', 'amount_due']


class BirthdaySerializer(serializers.Serializer):
    CUST_NO = serializers.CharField(max_length=20)
    ACCT_NO = serializers.CharField(max_length=20)
    ACCT_NM = serializers.CharField(max_length=100)
    CLIENT_TYPE = serializers.CharField(max_length=50)
    BU_CD = serializers.CharField(max_length=10)
    BU_NM = serializers.CharField(max_length=50)
    PROD_CD = serializers.CharField(max_length=10)
    PROD_DESC = serializers.CharField(max_length=100)
    CONTACT = serializers.CharField(max_length=15)
    EMAIL = serializers.CharField(allow_null=True, required=False)
    DATE_OF_BIRTH = serializers.DateTimeField(format='%Y-%m-%d')
    REC_ST = serializers.CharField(max_length=1)
    CREATE_DT = serializers.DateTimeField(format='%Y-%m-%d')

    def to_representation(self, instance):
        """
        Override this method to ensure that Decimal and DateTime objects are serialized correctly.
        """
        representation = super().to_representation(instance)

        representation['DATE_OF_BIRTH'] = instance['DATE_OF_BIRTH'].strftime('%Y-%m-%d') if isinstance(instance['DATE_OF_BIRTH'], datetime) else instance['DATE_OF_BIRTH']
        representation['CREATE_DT'] = instance['CREATE_DT'].strftime('%Y-%m-%d') if isinstance(instance['CREATE_DT'], datetime) else instance['CREATE_DT']

        return representation
    
class SendBirthdaySMSSerializer(serializers.Serializer):
    birthdays = BirthdaySerializer(many=True, required=True)


    def save(self, *args, **kwargs):

        data = self.validated_data
        birthdays = data.get('birthdays')

        response_data = []

        
        for birthday in birthdays:
            try:
                acct_nm = birthday.get('ACCT_NM')
                client_type = birthday.get('CLIENT_TYPE')
                date_of_birth = birthday.get('DATE_OF_BIRTH')
                contact = birthday.get('CONTACT')
                email = birthday.get('EMAIL')


                message = f"Dear {acct_nm}, Wishing you a very happy birthday from all of us at Pride Microfinance. May this special day bring you joy and Thank you for banking with us"

                BirthdayRequestsRequestDatatLogs.objects.create(
                        acct_nm = acct_nm,
                        client_type = client_type,
                        date_of_birth = date_of_birth,
                        contact = contact,
                        email = email
                )

                # Sending the SMS
                # resp = http.request(
                #     'GET',
                #     f"https://192.168.0.35/moonLight/SmsReceiver?sender_name=ibank&password=58c38dca-fc46-4018-a471-265cd7d98ab0&recipient_addr={tel_number}&message={message}"
                # )

                # if 'application/json' in resp.headers.get('Content-Type', ''):
                #     try:
                #         api_response = json.loads(resp.data.decode('utf-8'))
                #         # Log successful response
                #         SMSLog.objects.create(
                #             account_name=acct_nm,
                #             phone_number=tel_number,
                #             message=message,
                #             due_date=due_dt,
                #             amount_due=amt_due,
                #             status=api_response,
                #             response_data=api_response
                #         )
                #         response_data.append(api_response)
                #         # response_data.append(json.loads(resp.data.decode('utf-8')))
                #     except json.JSONDecodeError:
                #         response_data.append({"error": "Invalid JSON response"})
                #         SMSLog.objects.create(
                #             account_name=acct_nm,
                #             phone_number=tel_number,
                #             message=message,
                #             due_date=due_dt,
                #             amount_due=amt_due,
                #             status=api_response,
                #             response_data={"error": "Invalid JSON response"}
                #         )
                # else:
                #     response= resp.data.decode('utf-8')
                #     response_data.append({"error": "Non-JSON response received", "details": response})
                #     SMSLog.objects.create(
                #         account_name=acct_nm,
                #         phone_number=tel_number,
                #         message=message,
                #         due_date=due_dt,
                #         amount_due=amt_due,
                #         status=response,
                #         response_data={"error": "Non-JSON response received"}
                #     )

            except urllib3.exceptions.RequestError as e:
                response_data.append({"error": "Request failed", "details": str(e)})
                # SMSLog.objects.create(
                #     account_name=acct_nm,
                #     phone_number=tel_number,
                #     message=message,
                #     due_date=due_dt,
                #     amount_due=amt_due,
                #     status="Failed",
                #     response_data={"error": "Request failed", "details": str(e)}
                # )

            # Wait for 5 seconds before sending the next message
            time.sleep(5)

        return Response(response_data)