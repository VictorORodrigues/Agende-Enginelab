from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q

class DualAuthenticationBackend(ModelBackend):
    """
    Permite autenticação tanto pela Matrícula (username) quanto pelo E-mail.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            return None

        try:
            # Busca todos os usuários que batem com o username ou email
            users = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username))

            # Tenta autenticar cada um deles
            for user in users:
                if user.check_password(password):
                    return user

        except Exception:
            return None
        return None

    def user_can_authenticate(self, user):
        """
        Permite que o usuário seja 'autenticado' mesmo se estiver inativo,
        para que possamos mostrar a mensagem de 'Aguardando Aprovação' no formulário.
        """
        return True
