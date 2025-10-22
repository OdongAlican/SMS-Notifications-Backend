from rest_framework import serializers
from django.core.mail import EmailMessage
from rest_framework.response import Response
from datetime import datetime
from pride_notify_notice.models import SMSLog, BirthdaySMSLog
from .tasks import send_sms_to_api
from .utils import update_List, batch_save_responses
import urllib3
from django.conf import settings
import json

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
        http = urllib3.PoolManager()
        attachments = {f"attachments[{index}]":data for index,data in enumerate(attachments)}
        try:
            resp = http.request(
                'POST',
                f"{settings.API_NOTIFICATIONS}/email/",
                fields={
                    'sender_email': settings.SENDER_EMAIL,
                    'html_message': (self.validated_data.get("message") or self.validated_data.get("html_message")),
                    'subject': self.validated_data.get("subject"),
                    'to': self.validated_data.get("to"),
                    'attachments': attachments
                }
            )
            return json.loads(resp.data.decode('utf-8'))
        except Exception as e:
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

class IndividualMessageSerializer(serializers.Serializer):
    No = serializers.CharField(required=True)
    Name = serializers.CharField(required=True)
    Number = serializers.CharField(required=True)
    Message = serializers.CharField(required=True)


class SendSMSSerializer(serializers.Serializer):
    individualMessage = IndividualMessageSerializer(many=True, required=True)

    def save(self, *args, **kwargs):
        individual_messages = self.validated_data.get('individualMessage')
        print(individual_messages)
        
        task_results = []
        
        for message_data in individual_messages:
            # Format phone number - add country code if needed and clean non-breaking spaces
            phone_number = str(message_data['Number']).strip().replace('\xa0', '')
            
            # Add country code (256) if not present and remove leading zero if needed
            if phone_number.startswith('0'):
                phone_number = f"256{phone_number[1:]}"
            elif not phone_number.startswith('256'):
                phone_number = f"256{phone_number}"
            
            # Create a message detail object for the SMS API
            message_detail = {
                'CUST_NM': message_data['Name'],
                'TEL_NUMBER': phone_number,
                'CUSTOM_MESSAGE': message_data['Message']  # Use custom message field
            }
            
            # Send SMS using the API
            response = send_sms_to_api(message_detail)
            if response:
                task_results.append(response)
        
        # Save responses to database if applicable
        if task_results:
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
    DATE_OF_BIRTH = serializers.DateField(format='%Y-%m-%d')
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
        new_list = update_List(birthdays)

        task_results = []

        for loan in new_list:
            # task_results.append(send_sms_to_api.apply_async(args=[loan]))
            response = send_sms_to_api(loan)
            if response:
                task_results.append(response)

        batch_save_responses(task_results)
        
        return Response(task_results)
    
class BirthdaySMSLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = BirthdaySMSLog
        fields = ['id', 'acct_nm', 'client_type', 'status', 'created_at', 'response_data', 'date_of_birth', 'contact']