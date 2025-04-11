from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
import secrets
from datetime import timedelta
from .models import PrideUser
from django.contrib.auth.hashers import make_password
from .utils import send_email_notification


class ForgotPasswordRequestApi(APIView):
    """
    API to request a password reset.
    """

    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = PrideUser.objects.get(email=email)

            reset_token = secrets.token_urlsafe(64)

            user.password_reset_token = reset_token
            user.password_reset_token_expiry = timezone.now() + timedelta(hours=1)
            user.save()

            if send_email_notification(user, reset_token, "reset"):
                return Response(
                    {"message": "Password reset email has been sent."},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": "Failed to send email."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except PrideUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResetPasswordApi(APIView):
    """
    API to reset the password using a reset token.
    """

    def post(self, request):
        reset_token = request.data.get("reset_token")
        new_password = request.data.get("new_password")

        if not reset_token or not new_password:
            return Response({"error": "Reset token and new password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = PrideUser.objects.get(password_reset_token=reset_token)

            if user.password_reset_token_expiry < timezone.now():
                return Response({"error": "Reset token has expired."}, status=status.HTTP_400_BAD_REQUEST)

            user.password = make_password(new_password)
            user.password_reset_token = None
            user.password_reset_token_expiry = None
            user.save()

            return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)

        except PrideUser.DoesNotExist:
            return Response({"error": "Invalid reset token."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)