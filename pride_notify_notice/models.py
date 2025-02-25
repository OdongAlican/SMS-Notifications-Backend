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


class RequestDatatLogs(models.Model):
    account_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    message = models.TextField()
    due_date = models.DateField(null=True, blank=True)
    amount_due = models.FloatField()
    status = models.CharField(max_length=50)  # Success or Failed
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SMSLog for {self.account_name} ({self.phone_number})"
    

class BirthdayRequestsRequestDatatLogs(models.Model):
    acct_nm = models.CharField(max_length=255)
    client_type = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True, blank=True)
    contact = models.CharField(max_length=15)
    email = models.CharField(max_length=255)

    
    def __str__(self):
        return f"SMSLog for {self.acct_nm} ({self.contact})"

class BirthdaySMSLog(models.Model):
    acct_nm = models.CharField(max_length=255)
    client_type = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True, blank=True)
    contact = models.CharField(max_length=15)
    email = models.CharField(max_length=255)
    response_data = models.JSONField(null=True, blank=True)  # Store the API response
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SMSLog for {self.acct_nm} ({self.contact})"