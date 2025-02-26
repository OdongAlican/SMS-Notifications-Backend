from django.db import models

class SMSLog(models.Model):
    account_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    message = models.TextField()
    due_date = models.DateField(null=True, blank=True)
    amount_due = models.FloatField()
    status = models.CharField(max_length=50)
    response_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SMSLog for {self.account_name} ({self.phone_number})"

class BirthdaySMSLog(models.Model):
    acct_nm = models.CharField(max_length=255)
    client_type = models.CharField(max_length=255)
    message = models.TextField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    contact = models.CharField(max_length=15)
    response_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"BirthdaySMSLog for {self.acct_nm} ({self.contact})"