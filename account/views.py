from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.db import transaction
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.urls import reverse
from decouple import config
import logging
import secrets

from .forms import RegisterForm, LoginForm, SubAdminForm
from .models import Perfil
from .decorators import requer_admin

logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    authentication_form = LoginForm
    template_name = 'registration/login.html'


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    token = secrets.token_urlsafe(32)
                    perfil = user.perfil
                    perfil.token_aprovacao = token
                    perfil.save()

                aprovar_url = request.build_absolute_uri(
                    reverse('aprovar_via_token', kwargs={'token': token})
                )
                recusar_url = request.build_absolute_uri(
                    reverse('recusar_via_token', kwargs={'token': token})
                )
                send_mail(
                    f'Nova solicitação de cadastro — {user.get_full_name()}',
                    f'Novo cadastro de {user.get_full_name()} aguardando aprovação.',
                    config('EMAIL_HOST_USER'),
                    [config('EMAIL_ADMIN_LAB')],
                    html_message=render_to_string('emails/email_admin_notification.html', {
                        'user': user,
                        'aprovar_url': aprovar_url,
                        'recusar_url': recusar_url,
                    }),
                    fail_silently=True,
                )
                return redirect('aguardando_aprovacao')
            except ValidationError as exc:
                if hasattr(exc, 'message_dict'):
                    for field, errors in exc.message_dict.items():
                        for error in errors:
                            form.add_error(field if field in form.fields else None, error)
                else:
                    for msg in exc.messages:
                        form.add_error(None, msg)
            except Exception:
                messages.error(request, "Erro ao processar cadastro. Tente novamente.")
                logger.exception("Erro ao processar cadastro")
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def aguardando_aprovacao(request):
    return render(request, 'registration/aguardando_aprovacao.html')


def aprovar_via_token(request, token):
    perfil = Perfil.objects.filter(token_aprovacao=token).select_related('user').first()
    if not perfil:
        return render(request, 'registration/acao_ja_realizada.html', {'perfil': None})

    if perfil.status != Perfil.STATUS_PENDENTE:
        return render(request, 'registration/acao_ja_realizada.html', {'perfil': perfil})

    perfil.status = Perfil.STATUS_APROVADO
    perfil.token_aprovacao = None
    perfil.save()

    send_mail(
        'Seu cadastro foi aprovado — EngineLab UFC',
        f'Olá {perfil.user.first_name}, seu cadastro foi aprovado!',
        config('EMAIL_HOST_USER'),
        [perfil.user.email],
        html_message=render_to_string('emails/email_aprovado.html', {
            'user': perfil.user,
            'login_url': request.build_absolute_uri(reverse('login')),
        }),
        fail_silently=True,
    )
    return render(request, 'registration/resultado_aprovacao.html', {
        'perfil': perfil,
        'acao': 'aprovado',
    })


def recusar_via_token(request, token):
    perfil = Perfil.objects.filter(token_aprovacao=token).select_related('user').first()
    if not perfil:
        return render(request, 'registration/acao_ja_realizada.html', {'perfil': None})

    if perfil.status != Perfil.STATUS_PENDENTE:
        return render(request, 'registration/acao_ja_realizada.html', {'perfil': perfil})

    perfil.status = Perfil.STATUS_REJEITADO
    perfil.token_aprovacao = None
    perfil.save()

    send_mail(
        'Cadastro não aprovado — EngineLab UFC',
        f'Olá {perfil.user.first_name}, seu cadastro não foi aprovado.',
        config('EMAIL_HOST_USER'),
        [perfil.user.email],
        html_message=render_to_string('emails/email_recusado.html', {'user': perfil.user}),
        fail_silently=True,
    )
    return render(request, 'registration/resultado_aprovacao.html', {
        'perfil': perfil,
        'acao': 'recusado',
    })


@requer_admin
def admin_usuarios_pendentes(request):
    pendentes = Perfil.objects.filter(
        status=Perfil.STATUS_PENDENTE
    ).select_related('user', 'setor')
    return render(request, 'account/admin_usuarios_pendentes.html', {'pendentes': pendentes})


@requer_admin
def aprovar_usuario(request, pk):
    if request.method == 'POST':
        perfil = get_object_or_404(Perfil, pk=pk)
        perfil.status = Perfil.STATUS_APROVADO
        perfil.token_aprovacao = None
        perfil.save()
        send_mail(
            'Seu cadastro foi aprovado — EngineLab UFC',
            f'Olá {perfil.user.first_name}, seu cadastro foi aprovado!',
            config('EMAIL_HOST_USER'),
            [perfil.user.email],
            html_message=render_to_string('emails/email_aprovado.html', {
                'user': perfil.user,
                'login_url': request.build_absolute_uri(reverse('login')),
            }),
            fail_silently=True,
        )
        messages.success(request, f'Usuário {perfil.user.get_full_name()} aprovado.')
    return redirect('admin_usuarios_pendentes')


@requer_admin
def recusar_usuario(request, pk):
    if request.method == 'POST':
        perfil = get_object_or_404(Perfil, pk=pk)
        perfil.status = Perfil.STATUS_REJEITADO
        perfil.token_aprovacao = None
        perfil.save()
        send_mail(
            'Cadastro não aprovado — EngineLab UFC',
            f'Olá {perfil.user.first_name}, seu cadastro não foi aprovado.',
            config('EMAIL_HOST_USER'),
            [perfil.user.email],
            html_message=render_to_string('emails/email_recusado.html', {'user': perfil.user}),
            fail_silently=True,
        )
        messages.warning(request, f'Cadastro de {perfil.user.get_full_name()} recusado.')
    return redirect('admin_usuarios_pendentes')


@requer_admin
def admin_usuarios(request):
    status_selecionado = request.GET.get('status', '')
    perfis = Perfil.objects.select_related('user', 'setor').exclude(tipo='ADMIN')
    if status_selecionado:
        perfis = perfis.filter(status=status_selecionado)
    return render(request, 'account/admin_usuarios.html', {
        'perfis': perfis,
        'status_choices': Perfil.STATUS_CHOICES,
        'status_selecionado': status_selecionado,
    })


@requer_admin
def admin_subadmins(request):
    subadmins = Perfil.objects.filter(tipo='SUBADM').select_related('user').prefetch_related('permissoes')
    return render(request, 'account/admin_subadmins.html', {'subadmins': subadmins})


@requer_admin
def criar_subadmin(request):
    if request.method == 'POST':
        form = SubAdminForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'SubAdmin criado com sucesso.')
            return redirect('admin_subadmins')
    else:
        form = SubAdminForm()
    return render(request, 'account/subadmin_form.html', {'form': form, 'modo': 'criar'})


@requer_admin
def editar_subadmin(request, pk):
    perfil = get_object_or_404(Perfil, pk=pk, tipo='SUBADM')
    if request.method == 'POST':
        form = SubAdminForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, 'SubAdmin atualizado com sucesso.')
            return redirect('admin_subadmins')
    else:
        form = SubAdminForm(instance=perfil)
    return render(request, 'account/subadmin_form.html', {'form': form, 'modo': 'editar', 'subadmin': perfil})


@requer_admin
def excluir_subadmin(request, pk):
    perfil = get_object_or_404(Perfil, pk=pk, tipo='SUBADM')
    if request.method == 'POST':
        nome = perfil.user.get_full_name()
        perfil.user.delete()
        messages.success(request, f'SubAdmin {nome} excluído.')
        return redirect('admin_subadmins')
    return render(request, 'account/confirmar_exclusao_subadmin.html', {'subadmin': perfil})


@login_required
def pagina_em_construcao(request):
    titulo = request.GET.get('titulo', 'Página')
    return render(request, 'account/em_construcao.html', {'titulo': titulo})
