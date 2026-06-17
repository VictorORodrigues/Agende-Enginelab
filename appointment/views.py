from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from decouple import config

from account.models import Perfil
from account.decorators import requer_subadm
from .forms import AgendamentoForm
from .models import Agendamento


@login_required
def home(request):
    try:
        perfil = request.user.perfil
    except Perfil.DoesNotExist:
        perfil = Perfil.objects.create(user=request.user)

    if perfil.eh_aluno:
        return redirect('equipamentos')

    is_admin = perfil.eh_admin
    is_subadm = perfil.eh_subadm or is_admin

    return render(request, 'appointment/dashboard.html', {
        'perfil': perfil,
        'is_subadm': is_subadm,
        'is_admin': is_admin,
    })


@login_required
def meus_agendamentos(request):
    agendamentos = Agendamento.objects.filter(usuario=request.user).select_related('setor')
    return render(request, 'appointment/meus_agendamentos.html', {'agendamentos': agendamentos})


@login_required
def solicitar_agendamento(request):
    if request.method == 'POST':
        form = AgendamentoForm(request.POST)
        if form.is_valid():
            agendamento = form.save(commit=False)
            agendamento.usuario = request.user
            agendamento.save()
            messages.success(request, 'Agendamento solicitado com sucesso. Aguarde aprovação.')
            return redirect('appointment:meus_agendamentos')
    else:
        form = AgendamentoForm()
    return render(request, 'appointment/solicitar_agendamento.html', {'form': form})


@login_required
def cancelar_agendamento(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk, usuario=request.user)
    if request.method == 'POST':
        if agendamento.status in (Agendamento.STATUS_PENDENTE, Agendamento.STATUS_APROVADO):
            agendamento.status = Agendamento.STATUS_CANCELADO
            agendamento.save()
            messages.success(request, 'Agendamento cancelado.')
        else:
            messages.error(request, 'Este agendamento não pode ser cancelado.')
    return redirect('appointment:meus_agendamentos')


@requer_subadm
def gerenciar_agendamentos(request):
    perfil = request.user.perfil
    agendamentos = Agendamento.objects.filter(
        status=Agendamento.STATUS_PENDENTE
    ).select_related('setor', 'usuario')
    if perfil.eh_subadm and not perfil.eh_admin and perfil.setor:
        agendamentos = agendamentos.filter(setor=perfil.setor)
    return render(request, 'appointment/gerenciar_agendamentos.html', {'agendamentos': agendamentos})


@requer_subadm
def aprovar_agendamento(request, pk):
    if request.method == 'POST':
        agendamento = get_object_or_404(Agendamento, pk=pk, status=Agendamento.STATUS_PENDENTE)
        agendamento.status = Agendamento.STATUS_APROVADO
        agendamento.save()
        html_message = render_to_string('appointment/emails/email_agendamento_aprovado.html', {
            'agendamento': agendamento,
        })
        send_mail(
            'Agendamento aprovado - EngineLab UFC',
            f'Seu agendamento em {agendamento.setor} foi aprovado.',
            config('EMAIL_HOST_USER'),
            [agendamento.usuario.email],
            html_message=html_message,
            fail_silently=True,
        )
        messages.success(request, 'Agendamento aprovado.')
    return redirect('appointment:gerenciar_agendamentos')


@requer_subadm
def recusar_agendamento(request, pk):
    if request.method == 'POST':
        agendamento = get_object_or_404(Agendamento, pk=pk, status=Agendamento.STATUS_PENDENTE)
        agendamento.status = Agendamento.STATUS_RECUSADO
        agendamento.save()
        html_message = render_to_string('appointment/emails/email_agendamento_recusado.html', {
            'agendamento': agendamento,
        })
        send_mail(
            'Agendamento não aprovado - EngineLab UFC',
            f'Seu agendamento em {agendamento.setor} não foi aprovado.',
            config('EMAIL_HOST_USER'),
            [agendamento.usuario.email],
            html_message=html_message,
            fail_silently=True,
        )
        messages.warning(request, 'Agendamento recusado.')
    return redirect('appointment:gerenciar_agendamentos')
