# Generated by Django 5.1.4 on 2025-04-09 12:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_activetoken'),
    ]

    operations = [
        migrations.RenameField(
            model_name='activetoken',
            old_name='refresh_token',
            new_name='active_token',
        ),
    ]
