from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta

class PrideUser(AbstractUser):
    enabled = models.BooleanField(default=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    password_expiry_days = models.IntegerField(default=30)
    must_change_password = models.BooleanField(default=True)
    locked_until = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    title = models.CharField(null=True, max_length=200)

    def is_password_expired(self):
        """Check if password is expired."""
        if self.password_changed_at:
            expiry_date = self.password_changed_at + timedelta(days=self.password_expiry_days)
            return timezone.now() > expiry_date
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


class TokenHistory(models.Model):
    user = models.ForeignKey(PrideUser, on_delete=models.CASCADE)
    refresh_token = models.CharField(max_length=255, unique=False)
    access_token = models.CharField(max_length=255, unique=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Token history for {self.user.username} - Active: {self.is_active}"