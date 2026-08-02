from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.contrib import messages, auth
from django.core.mail import send_mail
from django.db import transaction
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.urls import reverse
from decouple import config
import logging
import secrets

from .forms import RegisterForm, LoginForm, SubAdminForm, SetorForm, CompleteSubAdminProfileForm

def completar_perfil_subadmin(request, uidb64, token):
    from django.utils.http import urlsafe_base64_decode
    from django.utils.encoding import force_str
    from django.contrib.auth.tokens import default_token_generator

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = CompleteSubAdminProfileForm(request.POST)
            if form.is_valid():
                nome = form.cleaned_data['nome_completo'].strip()
                partes = nome.split(' ', 1)
                user.first_name = partes[0]
                user.last_name = partes[1] if len(partes) > 1 else ''
                user.set_password(form.cleaned_data['senha'])
                user.is_active = True
                user.save()

                perfil = user.perfil
                perfil.telefone = form.cleaned_data['telefone']
                perfil.status = Perfil.STATUS_APROVADO
                perfil.save()

                messages.success(request, "Perfil configurado com sucesso! Você já pode entrar no sistema.")
                return redirect('login')
        else:
            form = CompleteSubAdminProfileForm()
        return render(request, 'account/completar_perfil_subadmin.html', {'form': form, 'email': user.email})
    else:
        return render(request, 'registration/invalid_link.html')
from .models import Perfil, Setor
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
    ).select_related('user')
    return render(request, 'account/admin_usuarios_pendentes.html', {'pendentes': pendentes})


@requer_admin
def aprovar_usuario(request, pk):
    if request.method == 'POST':
        perfil = get_object_or_404(Perfil, pk=pk)
        if perfil.status != Perfil.STATUS_PENDENTE:
            messages.info(request, f'O usuário {perfil.user.get_full_name()} já foi processado (Status: {perfil.get_status_display()}).')
            return redirect('admin_usuarios_pendentes')

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
        if perfil.status != Perfil.STATUS_PENDENTE:
            messages.info(request, f'O usuário {perfil.user.get_full_name()} já foi processado (Status: {perfil.get_status_display()}).')
            return redirect('admin_usuarios_pendentes')

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
    perfis = Perfil.objects.select_related('user').exclude(tipo='ADMIN')
    if status_selecionado:
        perfis = perfis.filter(status=status_selecionado)
    return render(request, 'account/admin_usuarios.html', {
        'perfis': perfis,
        'status_choices': Perfil.STATUS_CHOICES,
        'status_selecionado': status_selecionado,
    })


@requer_admin
def alterar_status_usuario(request, pk):
    if request.method == 'POST':
        perfil = get_object_or_404(Perfil, pk=pk)
        novo_status = request.POST.get('status')
        if novo_status in dict(Perfil.STATUS_CHOICES):
            old_status = perfil.status
            perfil.status = novo_status
            perfil.save()

            # Se mudou para aprovado e antes não era, pode mandar e-mail (opcional)
            if novo_status == Perfil.STATUS_APROVADO and old_status != Perfil.STATUS_APROVADO:
                 send_mail(
                    'Seu cadastro foi aprovado — EngineLab UFC',
                    f'Olá {perfil.user.first_name}, seu status foi alterado para Aprovado!',
                    config('EMAIL_HOST_USER'),
                    [perfil.user.email],
                    html_message=render_to_string('emails/email_aprovado.html', {
                        'user': perfil.user,
                        'login_url': request.build_absolute_uri(reverse('login')),
                    }),
                    fail_silently=True,
                )

            messages.success(request, f'Status de {perfil.user.get_full_name()} alterado para {perfil.get_status_display()}.')
    return redirect('admin_usuarios')


@requer_admin
def admin_subadmins(request):
    subadmins = Perfil.objects.filter(tipo='SUBADM').select_related('user').prefetch_related('setores_gerenciados')
    return render(request, 'account/admin_subadmins.html', {'subadmins': subadmins})


@requer_admin
def admin_setores(request):
    setores = Setor.objects.all().order_by('nome')
    return render(request, 'account/admin_setores.html', {'setores': setores})


@requer_admin
def setor_criar(request):
    if request.method == 'POST':
        form = SetorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Setor criado com sucesso.')
            return redirect('admin_setores')
    else:
        form = SetorForm()
    return render(request, 'account/setor_form.html', {'form': form, 'modo': 'criar'})


@requer_admin
def setor_editar(request, pk):
    setor = get_object_or_404(Setor, pk=pk)
    if request.method == 'POST':
        form = SetorForm(request.POST, instance=setor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Setor atualizado com sucesso.')
            return redirect('admin_setores')
    else:
        form = SetorForm(instance=setor)
    return render(request, 'account/setor_form.html', {'form': form, 'modo': 'editar', 'setor': setor})


@requer_admin
def setor_excluir(request, pk):
    setor = get_object_or_404(Setor, pk=pk)
    if request.method == 'POST':
        nome = setor.nome
        try:
            setor.delete()
            messages.success(request, f'Setor {nome} excluído.')
        except Exception:
            messages.error(request, 'Não é possível excluir este setor pois existem dados vinculados a ele.')
        return redirect('admin_setores')
    return render(request, 'account/confirmar_exclusao_setor.html', {'setor': setor})


from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

@requer_admin
def criar_subadmin(request):
    if request.method == 'POST':
        form = SubAdminForm(request.POST)
        if form.is_valid():
            subadmin, criado = form.save()

            # Jurisdições formatadas para o e-mail
            jurisdicoes_dados = []
            for jur in subadmin.jurisdicoes.all():
                jurisdicoes_dados.append({
                    'setor': jur.setor.nome,
                    'itens': jur.pode_gerenciar_itens,
                    'emprestimos': jur.pode_gerenciar_emprestimos
                })

            if criado:
                # Caso 1: Usuário novo (ENVIA CONVITE PARA COMPLETAR PERFIL)
                token = default_token_generator.make_token(subadmin.user)
                uid = urlsafe_base64_encode(force_bytes(subadmin.user.pk))
                reset_link = request.build_absolute_uri(
                    reverse('completar_perfil_subadmin', kwargs={'uidb64': uid, 'token': token})
                )

                html_message = render_to_string('emails/email_convite_subadmin.html', {
                    'permissoes': [f"{j['setor']} ({'Itens' if j['itens'] else ''}{', ' if j['itens'] and j['emprestimos'] else ''}{'Empréstimos' if j['emprestimos'] else ''})" for j in jurisdicoes_dados],
                    'reset_link': reset_link,
                })

                send_mail(
                    'Convite: Você é o novo Sub-Administrador do EngineLab',
                    'Você agora é um sub-administrador.',
                    config('EMAIL_HOST_USER'),
                    [subadmin.user.email],
                    html_message=html_message,
                    fail_silently=True,
                )
                messages.success(request, f'Convite enviado com sucesso para {subadmin.user.email}.')
            else:
                # Caso 2: Usuário já existia (ENVIA PROMOÇÃO COM LOGIN ATUAL)
                login_url = request.build_absolute_uri(reverse('login'))
                html_message = render_to_string('emails/email_promocao_subadmin.html', {
                    'nome': subadmin.user.first_name or 'Sub-Administrador',
                    'jurisdicoes': jurisdicoes_dados,
                    'login_url': login_url,
                })

                send_mail(
                    'Promoção: Nova função administrativa no EngineLab',
                    'Seu perfil foi promovido a sub-administrador.',
                    config('EMAIL_HOST_USER'),
                    [subadmin.user.email],
                    html_message=html_message,
                    fail_silently=True,
                )
                messages.success(request, f'Usuário {subadmin.user.email} promovido a SubAdmin com sucesso.')

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
        nome = perfil.user.get_full_name() or perfil.user.email
        with transaction.atomic():
            # 1. Remove todas as jurisdições específicas por setor
            perfil.jurisdicoes.all().delete()
            # 2. Rebaixa para ALUNO
            perfil.tipo = 'ALUNO'
            perfil.save()
        messages.success(request, f'Privilégios administrativos de {nome} revogados com sucesso. O usuário agora é um Aluno comum.')
        return redirect('admin_subadmins')
    return render(request, 'account/confirmar_exclusao_subadmin.html', {'subadmin': perfil})


@login_required
def excluir_conta(request):
    if request.method == 'POST':
        user = request.user
        auth.logout(request)
        user.delete()
        messages.success(request, 'Sua conta foi excluída com sucesso.')
        return redirect('login')
    return redirect('admin_equipamentos')


@login_required
def pagina_em_construcao(request):
    titulo = request.GET.get('titulo', 'Página')
    return render(request, 'account/em_construcao.html', {'titulo': titulo})
