from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import login     
from .forms import RegistroForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Equipamento, Emprestimo, FilaEspera

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['senha'])
            # Opcional: user.is_active = False (Para o professor ter que aprovar manualmente)
            user.save()
            messages.success(request, "Cadastro realizado! Faça login.")
            return redirect('login')
    else:
        form = RegistroForm()
    return render(request, 'registration/registro.html', {'form': form})

@login_required
def dashboard(request):
    equipamentos = Equipamento.objects.all()
    return render(request, 'core/dashboard.html', {'equipamentos': equipamentos})

def solicitar_emprestimo(request, eq_id):
    # Deixe essa função vazia por enquanto só para não dar erro de importação
    pass