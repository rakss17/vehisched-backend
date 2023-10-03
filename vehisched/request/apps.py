from django.apps import AppConfig


class RequestConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'request'

    def ready(self):
        import request.signals