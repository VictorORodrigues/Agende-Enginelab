from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def requer_admin(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        perfil = getattr(request.user, 'perfil', None)
        if not (perfil and perfil.eh_admin):
            messages.error(request, 'Você não tem permissão para acessar esta área.')
            return redirect('admin_equipamentos')
        return view_func(request, *args, **kwargs)
    return _wrapped


def requer_subadm(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        perfil = getattr(request.user, 'perfil', None)
        if not (perfil and (perfil.eh_subadm or perfil.eh_admin)):
            messages.error(request, 'Você não tem permissão para acessar esta área.')
            return redirect('admin_equipamentos')
        return view_func(request, *args, **kwargs)
    return _wrapped


def requer_permissao_subadmin(escopo):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            perfil = getattr(request.user, 'perfil', None)
            if not (perfil and perfil.tem_permissao(escopo)):
                messages.error(request, 'Você não tem permissão para acessar esta área.')
                return redirect('admin_equipamentos')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
