from django.shortcuts import render
from .forms import RegisterForm
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.models import User
from decouple import config
from django.db import transaction
from django.contrib import messages
from django.urls import reverse
import logging
from .models import Perfil

logger = logging.getLogger(__name__)

# ===============================
# USER REGISTRATION
# ===============================
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    token = default_token_generator.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    activation_link = request.build_absolute_uri(
                        reverse('activate_account', kwargs={'uidb64': uid, 'token': token})
                    )

                    context = {
                        'name': user.first_name,
                        'link': activation_link,
                    }

                    html_content = render_to_string('emails/email_activation.html', context)

                    send_mail(
                        'Ative sua conta - EngineLab',
                        f"Olá {user.first_name}, ative sua conta: {activation_link}",
                        config('EMAIL_HOST_USER'),
                        [user.email],
                        html_message=html_content,
                        fail_silently=False, 
                    )

                return render(request, 'registration/activate_account/confirmation_sent.html')
            except ValidationError as exc:
                if hasattr(exc, 'message_dict'):
                    for field, errors in exc.message_dict.items():
                        for error in errors:
                            form.add_error(field if field in form.fields else None, error)
                else:
                    for message in exc.messages:
                        form.add_error(None, message)
            except Exception:
                messages.error(request, f"Erro ao processar cadastro: Verifique sua conexão ou as configurações de e-mail.")
                logger.exception("Erro ao processar cadastro")

    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})

# ===============================
# ACCOUNT ACTIVATION
# ===============================
def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        perfil = user.perfil

        if perfil.status == Perfil.STATUS_PENDENTE_EMAIL:
            perfil.status = Perfil.STATUS_PENDENTE_APROVACAO
            perfil.save()

            admin_url = request.build_absolute_uri(reverse('admin:auth_user_change', args=[user.id]))
            html_message = render_to_string('emails/email_admin_notification.html', {
                'user': user,
                'admin_url': admin_url,
            })

            send_mail(
                'Nova Solicitação de Cadastro',
                f'Aprovar {user.get_full_name()} em {admin_url}',
                config('EMAIL_HOST_USER'),
                [config('EMAIL_HOST_USER')],
                html_message=html_message
            )
            return render(request, 'registration/activate_account/waiting_approval.html', {
                'user': user,
                'status_message': 'Seu e-mail foi confirmado e sua conta aguarda aprovação do administrador.',
            })

        if perfil.status == Perfil.STATUS_PENDENTE_APROVACAO:
            return render(request, 'registration/activate_account/waiting_approval.html', {
                'user': user,
                'status_message': 'Seu e-mail já foi confirmado. Sua conta continua aguardando aprovação do administrador.',
            })

        return render(request, 'registration/activate_account/waiting_approval.html', {
            'user': user,
            'status_message': 'Sua conta já está ativa. Você já pode entrar no sistema.',
        })
    return render(request, 'registration/invalid_link.html')
