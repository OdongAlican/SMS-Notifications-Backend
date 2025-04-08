# trails/apps.py
from django.apps import AppConfig

class TrailsConfig(AppConfig):
    name = 'trails'

    def ready(self):
        import trails.signals  # Import the signals to register them
