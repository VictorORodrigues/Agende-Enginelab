from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    # Aqui você já pode filtrar o que cada um vê
    if request.user.perfil.eh_aluno:
        return render(request, 'appointment/studant_home.html')
    elif request.user.perfil.eh_subadm:
        return render(request, 'appointment/subadm_home.html')
    return render(request, 'appointment/admin_home.html')
