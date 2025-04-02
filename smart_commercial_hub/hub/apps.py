# hub/apps.py

from django.apps import AppConfig

class HubConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hub'

    def ready(self):
        import hub.signals  # Import the signals when the app starts
