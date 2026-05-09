from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from account.models import Perfil

@login_required
def home(request):
    try:
        perfil = request.user.perfil
    except Perfil.DoesNotExist:
        perfil = Perfil.objects.create(user=request.user)

    is_admin = perfil.eh_admin
    is_subadm = perfil.eh_subadm or is_admin
    is_student = perfil.eh_aluno

    return render(
        request,
        'appointment/dashboard.html',
        {
            'perfil': perfil,
            'is_student': is_student,
            'is_subadm': is_subadm,
            'is_admin': is_admin,
        },
    )
