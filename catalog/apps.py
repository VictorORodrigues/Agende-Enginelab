from django.apps import AppConfig


class CatalogConfig(AppConfig):
    name = 'catalog'

    def ready(self):
        import os
        # Garante que o agendador só inicie no processo principal
        if os.environ.get('RUN_MAIN'):
            from . import updater
            updater.start()
