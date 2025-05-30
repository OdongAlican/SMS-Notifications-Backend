from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password, make_password

class PrideUser(AbstractUser):
    enabled = models.BooleanField(default=False)  # Default set to False for new users
    password_changed_at = models.DateTimeField(null=True, blank=True)
    password_expiry_days = models.IntegerField(default=30)  # The default password expiry duration
    must_change_password = models.BooleanField(default=True)
    locked_until = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    title = models.CharField(null=True, max_length=200)
    temporary_password_expiry = models.DateTimeField(null=True, blank=True)  # Temporary password expiration
    password_reset_token = models.CharField(max_length=128, null=True, blank=True)
    password_reset_token_expiry = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    is_deactivated = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """Override save method to set enabled to False when the user is first created and set temporary password expiration."""
        if self._state.adding:  # Check if it's a new object being created
            self.enabled = False  # Set enabled to False for newly created users
            # self.temporary_password_expiry = timezone.now() + timedelta(hours=1)  # Set temporary password expiration to 1 hour
            self.temporary_password_expiry = timezone.now() + timedelta(minutes=5)  # Set temporary password expiration to 5 minutes
        super().save(*args, **kwargs)

    def is_password_expired(self):
        """Check if normal password is expired (after 180 days)."""
        if self.password_changed_at:
            expiry_date = self.password_changed_at + timedelta(days=180)
            return timezone.now() > expiry_date
        return False

    def is_temporary_password_expired(self):
        """Check if temporary password is expired (after 1 hour)."""
        if self.temporary_password_expiry:
            return timezone.now() > self.temporary_password_expiry
        return False

    def lock_user(self):
        """Lock the user account."""
        self.is_locked = True
        self.locked_until = timezone.now() + timezone.timedelta(minutes=600)
        self.save()

    def unlock_user(self):
        """Unlock the user account."""
        self.is_locked = False
        self.locked_until = None
        self.save()

    def change_password(self, new_password):
        """Handle password change logic with secure history tracking."""
        # if self.is_temporary_password_expired():
        #     raise ValueError("Your temporary password has expired. Please contact the admin to reset it.")

        # Check if normal password has expired
        if self.is_password_expired():
            raise ValueError("Your password has expired. Please change your password.")

        # Check for password reuse constraint
        self.check_password_reuse(new_password)

        # Hash the new password before saving to history or user model
        hashed_new_password = make_password(new_password)

        # Save the *new hashed* password into PasswordHistory
        PasswordHistory.objects.create(user=self, password=hashed_new_password)

        # Apply new password to user
        self.password = hashed_new_password
        self.password_changed_at = timezone.now()
        self.enabled = True
        self.save()

    def check_password_reuse(self, new_password):
        """Check if the new password is being reused within the last 5 passwords and 180 days."""
        # Get the last 5 passwords and their change dates
        recent_passwords = PasswordHistory.objects.filter(user=self).order_by('-created_at')[:5]

        for password_history in recent_passwords:
            if check_password(new_password, password_history.password):
                if (timezone.now() - password_history.created_at).days < 180:
                    raise ValidationError("You cannot reuse a password that was used in the last 180 days or within the last 6 passwords.")

class PasswordHistory(models.Model):
    user = models.ForeignKey(PrideUser, on_delete=models.CASCADE)
    password = models.CharField(max_length=255)  # Store the hashed password
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Password history for {self.user.username} - {self.created_at}"

class TokenHistory(models.Model):
    user = models.ForeignKey(PrideUser, on_delete=models.CASCADE)
    refresh_token = models.CharField(max_length=255, unique=False)
    access_token = models.CharField(max_length=255, unique=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Token history for {self.user.username} - Active: {self.is_active}"