from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Agendamento
from .forms import AgendamentoForm
from account.decorators import requer_subadm
from account.models import Setor
from datetime import date, timedelta

@login_required
def meus_agendamentos(request):
    agendamentos = Agendamento.objects.filter(usuario=request.user).select_related('setor')
    return render(request, 'appointment/meus_agendamentos.html', {'agendamentos': agendamentos})

@login_required
def solicitar_agendamento(request):
    from catalog.models import Equipamento, Livro

    eq_id = request.GET.get('equipamento')
    liv_id = request.GET.get('livro')

    pre_item = None
    if eq_id:
        pre_item = get_object_or_404(Equipamento, pk=eq_id)
    elif liv_id:
        pre_item = get_object_or_404(Livro, pk=liv_id)

    if request.method == 'POST':
        form = AgendamentoForm(request.POST)
        if form.is_valid():
            agendamento = form.save(commit=False)
            agendamento.usuario = request.user

            if pre_item:
                if eq_id: agendamento.equipamento = pre_item
                else: agendamento.livro = pre_item
                agendamento.setor = pre_item.setor

            # Validação de conflito com empréstimo ativo
            from catalog.models import Emprestimo
            filtros = {'status': Emprestimo.STATUS_ATIVO}
            if agendamento.equipamento:
                filtros['equipamento'] = agendamento.equipamento
            else:
                filtros['livro'] = agendamento.livro

            # Se tiver data_final, valida o intervalo. Se não, valida apenas o dia de início.
            fim_agendamento = agendamento.data_final or agendamento.data

            conflito = Emprestimo.objects.filter(
                **filtros
            ).filter(
                Q(data_inicio__range=(agendamento.data, fim_agendamento)) |
                Q(data_final__range=(agendamento.data, fim_agendamento)) |
                Q(data_inicio__lte=agendamento.data, data_final__gte=fim_agendamento)
            ).exists()

            if conflito:
                form.add_error(None, "Este item já estará emprestado em parte do período selecionado.")
            else:
                agendamento.save()
                messages.success(request, 'Agendamento realizado com sucesso!')
                return redirect('appointment:meus_agendamentos')
    else:
        initial = {}
        if pre_item:
            initial['setor'] = pre_item.setor
        form = AgendamentoForm(initial=initial)
        if pre_item:
            form.fields['setor'].widget.attrs['disabled'] = True
            form.fields['setor'].required = False

    return render(request, 'appointment/solicitar_agendamento.html', {
        'form': form,
        'pre_item': pre_item
    })

@login_required
def cancelar_agendamento(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk, usuario=request.user)
    if agendamento.status in (Agendamento.STATUS_PENDENTE, Agendamento.STATUS_APROVADO):
        if request.method == 'POST':
            agendamento.status = Agendamento.STATUS_CANCELADO
            agendamento.save()
            messages.success(request, 'Agendamento cancelado com sucesso.')
            return redirect('appointment:meus_agendamentos')
        return render(request, 'appointment/confirmar_cancelamento.html', {'agendamento': agendamento})
    else:
        messages.error(request, 'Este agendamento não pode ser cancelado.')
        return redirect('appointment:meus_agendamentos')

@requer_subadm
def gerenciar_agendamentos(request):
    perfil = request.user.perfil
    qs = Agendamento.objects.select_related('usuario', 'setor', 'equipamento', 'livro').all()

    if not perfil.eh_admin:
        # Filtra setores sob jurisdição
        setores_permitidos = perfil.jurisdicoes.values_list('setor', flat=True)
        qs = qs.filter(setor_id__in=setores_permitidos)
    else:
        setores_permitidos = Setor.objects.all().values_list('id', flat=True)

    # Filtros
    search_query = request.GET.get('q', '')
    setor_id = request.GET.get('setor')
    status = request.GET.get('status')
    data_agendamento = request.GET.get('data')

    if search_query:
        qs = qs.filter(
            Q(usuario__first_name__icontains=search_query) |
            Q(usuario__username__icontains=search_query) |
            Q(equipamento__nome__icontains=search_query) |
            Q(livro__titulo__icontains=search_query)
        )
    if setor_id:
        qs = qs.filter(setor_id=setor_id)
    if status:
        qs = qs.filter(status=status)
    if data_agendamento:
        qs = qs.filter(data=data_agendamento)

    setores = Setor.objects.filter(id__in=setores_permitidos).order_by('nome')

    return render(request, 'appointment/gerenciar_agendamentos.html', {
        'agendamentos': qs,
        'setores': setores,
        'status_choices': Agendamento.STATUS_CHOICES,
        'search_query': search_query,
        'setor_selecionado': setor_id,
        'status_selecionado': status,
        'data_selecionada': data_agendamento
    })

@requer_subadm
def aprovar_agendamento(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk)
    if request.method == 'POST':
        agendamento.status = Agendamento.STATUS_APROVADO
        agendamento.save()
        messages.success(request, f'Agendamento de {agendamento.usuario.get_full_name()} aprovado.')
    return redirect('appointment:gerenciar_agendamentos')

@requer_subadm
def recusar_agendamento(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk)
    if request.method == 'POST':
        agendamento.status = Agendamento.STATUS_RECUSADO
        agendamento.save()
        messages.success(request, f'Agendamento de {agendamento.usuario.get_full_name()} recusado.')
    return redirect('appointment:gerenciar_agendamentos')
