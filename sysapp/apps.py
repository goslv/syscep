from django.apps import AppConfig

class SysappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sysapp'
    verbose_name = 'Sistema CEP'

    def ready(self):
        # Importar signals cuando la app esté lista
        import sysapp.signals
