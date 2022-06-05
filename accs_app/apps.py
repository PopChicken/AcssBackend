from django.apps import AppConfig


class AccsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accs_app'

    def ready(self) -> None:
        from accs_app.service.schd import on_init as on_schd_init
        on_schd_init()
