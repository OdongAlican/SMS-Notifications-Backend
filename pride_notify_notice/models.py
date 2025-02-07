from django.db import models

class SMSLog(models.Model):
    account_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    message = models.TextField()
    due_date = models.DateField(null=True, blank=True)
    amount_due = models.FloatField()
    status = models.CharField(max_length=50)  # Success or Failed
    response_data = models.JSONField(null=True, blank=True)  # Store the API response
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SMSLog for {self.account_name} ({self.phone_number})"
