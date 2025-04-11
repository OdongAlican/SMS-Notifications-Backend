import secrets
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .models import PrideUser, TokenHistory
from rest_framework import exceptions
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from rest_framework.views import APIView
from datetime import timedelta
from rest_framework_simplejwt.exceptions import TokenError
from .serializers import UserSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .utils import send_email_notification

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            raise exceptions.AuthenticationFailed("Username and password are required.")

        user = authenticate(username=username, password=password)

        if user is None:
            raise exceptions.AuthenticationFailed("Invalid credentials")

        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        # Deactivate any active tokens for the user to prevent concurrency
        # This ensures only the most recent login will have active tokens
        TokenHistory.objects.filter(user=user, is_active=True).update(is_active=False)

        # Store the new refresh token and access token in the TokenHistory model
        token_history = TokenHistory.objects.create(
            user=user,
            refresh_token=str(refresh),
            access_token=str(access_token),
            is_active=True
        )

        user_data = UserSerializer(user).data

        response_data = {
            "refresh": str(refresh),
            "access": str(access_token),
            "user": user_data,
            "token_history_id": token_history.id,
        }

        return Response(response_data)
    
class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):

        refresh_token = request.data.get('refresh')

        if not refresh_token:
            raise exceptions.AuthenticationFailed("Refresh token is required.")

        try:
            # Decode the refresh token
            refresh = RefreshToken(refresh_token)
            print(f"Decoded refresh token: {refresh}")

            # Extract user_id from token payload
            user_id = refresh['user_id']  # Adjust this if you use a different claim for user identification
            print(f"User ID from refresh token: {user_id}")

            # Get the user object
            user = PrideUser.objects.get(id=user_id)  # Query the user based on the user_id
            print(f"User from database: {user}")

            # Deactivate the old refresh token
            TokenHistory.objects.filter(user=user, refresh_token=refresh_token, is_active=True).update(is_active=False)

            # Create new access token
            access_token = refresh.access_token

            # Store the new token in the TokenHistory
            TokenHistory.objects.create(
                user=user,
                access_token=str(access_token),
                refresh_token=refresh_token,
                is_active=True
            )

            return Response({
                "access": str(access_token),
                "refresh": str(refresh_token),
            })

        except TokenError as e:
            print(f"TokenError: {e}")
            raise exceptions.AuthenticationFailed("Invalid refresh token.")
        except PrideUser.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found.")
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise exceptions.AuthenticationFailed("An error occurred while refreshing the token.")
        
class PasswordResetRequestView(APIView):
    
    def post(self, request):
        """
        Change the password of a user. The user needs to provide their current password
        and the new password.
        """
        try:
            user_id = request.data.get('user_id')
            user = PrideUser.objects.get(id=user_id)
            current_password = request.data.get('current_password')
            new_password = request.data.get('new_password')
                
            if not current_password or not new_password:
                return Response({"error": "Both current and new passwords are required."}, status=status.HTTP_400_BAD_REQUEST)

            # Authenticate user with current password
            if not user.check_password(current_password):
                return Response({"error": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

            # Call the custom change_password method
            user.change_password(new_password)

            return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
            
        except PrideUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ResetTemporaryPasswordApi(APIView):
    """
    API for a super admin to send a new temporary password to a user.
    """
    permission_classes = [IsAuthenticated]  # You can restrict this to super admin group permissions if needed.
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        """
        Reset the temporary password for a user if the current temporary password has expired.
        """
        try:
            # Get the user by ID
            user_id = request.data.get('user_id')
            user = PrideUser.objects.get(id=user_id)

            # Check if the temporary password has expired
            if not user.is_temporary_password_expired():
                return Response(
                    {"message": "Temporary password is still valid."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate a new temporary password
            temp_password = secrets.token_urlsafe(12)
            hashed_password = make_password(temp_password)

            # Update the user with the new temporary password and set expiration to 1 hour from now
            user.password = hashed_password
            # user.temporary_password_expiry = timezone.now() + timedelta(hours=1)
            user.temporary_password_expiry = timezone.now() + timedelta(minutes=5)
            user.save()

            # Send the temporary password to the user via email
            if send_email_notification(user, temp_password, "authentication"):
                return Response(
                    {"message": "New temporary password sent to the user."},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": "User created, but email could not be sent."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except PrideUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)