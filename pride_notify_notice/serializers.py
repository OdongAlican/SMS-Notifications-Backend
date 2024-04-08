from rest_framework import serializers
from django.core.mail import EmailMessage
import urllib3
import json
from rest_framework.response import Response
from pride_notify_service import settings
from urllib.parse import quote as url_quote


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


class SendSMSSerializer(serializers.Serializer):
    phonenumber = serializers.CharField(required=True)
    textmessage = serializers.CharField(required=True)

    def save(self, *args):
        data = self.validated_data
        text_message = url_quote(data.get('textmessage'))
        extras = f"textmessage={text_message}&phonenumber={data.get('phonenumber')}"
        http = urllib3.PoolManager()
        resp = http.request(
            'GET',
            f"{settings.SMS_URL}?api_id={settings.SMS_API_ID}&api_password={settings.SMS_API_PASS}&sms_type=P&encoding=T&sender_id={settings.SMS_SENDER_ID}&{extras}"
        )
        return Response(json.loads(resp.data.decode('utf-8')))