from django.apps import AppConfig
from django.conf import settings


class AccountConfig(AppConfig):
    name = 'account'

    def ready(self):
        if not settings.DEBUG:
            return
        # runserver serve estáticos via StaticFilesHandler, que ignora o
        # middleware por completo — sem isso o Chrome guarda a versão antiga
        # de CSS/JS/imagens em cache heurístico e nem faz nova requisição
        # quando os arquivos mudam.
        from django.contrib.staticfiles import handlers

        original_serve = handlers.serve

        def serve_no_cache(request, *args, **kwargs):
            response = original_serve(request, *args, **kwargs)
            response['Cache-Control'] = 'no-cache, must-revalidate'
            return response

        handlers.serve = serve_no_cache
