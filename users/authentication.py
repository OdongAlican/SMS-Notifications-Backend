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
from .utils import send_email_notification, IsTokenValid

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            raise exceptions.AuthenticationFailed("Username and password are required.")

        try:
            user = PrideUser.objects.get(username=username)
        except PrideUser.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid credentials")
        
        if user.is_deactivated:
            raise exceptions.AuthenticationFailed("Your Account has been deactivated. Please contact Admin")

        # Check if user is locked and if the lock period is still active
        if user.is_locked and user.locked_until and user.locked_until > timezone.now():
            remaining = (user.locked_until - timezone.now()).seconds // 60
            raise exceptions.AuthenticationFailed(f"Account is locked. Try again in {remaining} minutes or contact admin.")
        
        # Authenticate user
        user = authenticate(username=username, password=password)

        if user is None:
            # Increment failed login attempts only if user exists

            # Get the updated user object after incrementing
            user = PrideUser.objects.get(username=username)
            user.failed_login_attempts += 1
            # Lock the account after 3 failed attempts
            if user.failed_login_attempts >= 3:
                user.is_locked = True
                user.locked_until = timezone.now() + timedelta(hours=1)

            user.save()
            raise exceptions.AuthenticationFailed("Invalid credentials. Your account will be locked after 3 Invalid attempts")

        # If login successful: reset failed login attempts
        user.failed_login_attempts = 0
        user.is_locked = False
        user.locked_until = None
        user.save()

        # Issue tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        # Deactivate any active tokens for the user
        TokenHistory.objects.filter(user=user, is_active=True).update(is_active=False)

        # Save new tokens
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

            # Extract user_id from token payload
            user_id = refresh['user_id']  # Adjust this if you use a different claim for user identification

            # Get the user object
            user = PrideUser.objects.get(id=user_id)  # Query the user based on the user_id

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
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        """
        Reset the temporary password for a user if the current temporary password has expired.
        """
        try:
            user_id = request.data.get('user_id')
            user = PrideUser.objects.get(id=user_id)

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
        
class UnlockUserAccountView(APIView):
    """
    API view that allows a super admin to unlock a user account.
    This is intended to be used in cases where the user cannot wait for the lock period to expire.
    """
    permission_classes = [IsAuthenticated, IsTokenValid]
    authentication_classes = [JWTAuthentication]
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")

        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = PrideUser.objects.get(id=user_id)
        except PrideUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if not user.is_locked:
            return Response({"message": "User account is not locked."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_locked = False
        user.locked_until = None
        user.failed_login_attempts = 0
        user.save()

        return Response({"message": f"User {user.username} has been unlocked."}, status=status.HTTP_200_OK)

class DeactivateUserAccountView(APIView):
    """
    API view that allows a super admin to deactivate a user account.
    This is intended to be used in cases where the user account needs to be deactivated.
    """
    permission_classes = [IsAuthenticated, IsTokenValid]
    authentication_classes = [JWTAuthentication]
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")

        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = PrideUser.objects.get(id=user_id)
        except PrideUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_deactivated:
            return Response({"message": "User account is already deactivated."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_deactivated = True
        user.save()

        return Response({"message": f"User {user.username} has been deactivated."}, status=status.HTTP_200_OK)
    
class ActivateUserAccountView(APIView):
    """
    API view that allows a super admin to reactivate a user account.
    This is intended to be used in cases where the user account was previously deactivated.
    """
    permission_classes = [IsAuthenticated, IsTokenValid]
    authentication_classes = [JWTAuthentication]
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")

        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = PrideUser.objects.get(id=user_id)
        except PrideUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if not user.is_deactivated:
            return Response({"message": "User account is already activated."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_deactivated = False
        user.save()

        return Response({"message": f"User {user.username} has been reactivated."}, status=status.HTTP_200_OK)