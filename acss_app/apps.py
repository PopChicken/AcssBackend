import os

from django.apps import AppConfig


class acssAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'acss_app'

    def ready(self) -> None:
        if os.environ.get('RUN_MAIN', None) != 'true':
            return
        from acss_app.service.schd import on_init as on_schd_init
        on_schd_init()
