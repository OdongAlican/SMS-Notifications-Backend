from pride_notify_notice.serializers import SendEmailSerializer, SendSMSSerializer
import urllib3
import json
from rest_framework.response import Response
from rest_framework.request import Request
from pride_notify_service import settings
from rest_framework import views
from rest_framework import status
from urllib.parse import quote as url_quote


# Create your views here.
class Sms(views.APIView):
    def post(self, request: Request):
        serializer = SendSMSSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.save()


class Email(views.APIView):
    def post(self, request: Request) -> Response:
        serializer = SendEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "success": 1,
            "message": "Email has been sent successfully"}, status=status.HTTP_200_OK)
