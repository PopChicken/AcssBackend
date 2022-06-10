import os

from django.apps import AppConfig


init_flag = True


class acssAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'acss_app'

    def ready(self) -> None:
        global init_flag
        if init_flag is False:
            return
        init_flag = False
        from acss_app.service.schd import on_init as on_schd_init
        on_schd_init()
