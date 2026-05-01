from django.shortcuts import render
from .forms import RegisterForm
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User
from decouple import config
from django.db import transaction
from django.contrib import messages

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
                    user.is_active = False
                    user.save()
                    token = default_token_generator.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    domain = get_current_site(request).domain
                    activation_link = f"http://{domain}/activate/{uid}/{token}/"

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

            except Exception as e:
                messages.error(request, f"Erro ao processar cadastro: Verifique sua conexão ou as configurações de e-mail.")
                print(f"Erro de registro: {e}") 

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
    except: user = None

    if user and default_token_generator.check_token(user, token):
        # Gerar link do admin
        domain = get_current_site(request).domain
        admin_url = f"http://{domain}/admin/auth/user/{user.id}/change/"
        
        # Enviar e-mail ao Admin
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
        return render(request, 'registration/activate_account/waiting_approval.html', {'user': user})
    return render(request, 'registration/invalid_link.html')