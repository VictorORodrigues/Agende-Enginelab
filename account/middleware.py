from django.contrib import auth
from django.shortcuts import redirect
from django.contrib import messages

class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Forçamos a recarga do usuário do banco para garantir que temos o status mais recente
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(pk=request.user.pk)
            except User.DoesNotExist:
                auth.logout(request)
                return redirect('login')

            if not user.is_active:
                auth.logout(request)
                messages.error(request, "Você foi desconectado da conta por um administrador.")
                return redirect('login')

            perfil = getattr(user, 'perfil', None)
            if perfil and perfil.status == 'rejeitado':
                auth.logout(request)
                messages.error(request, "Você foi desconectado da conta por um administrador.")
                return redirect('login')

        response = self.get_response(request)
        return response
