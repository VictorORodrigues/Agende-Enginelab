from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate

class RegisterForm(forms.ModelForm):
    first_name = forms.CharField(label="Nome Completo", max_length=150)
    email = forms.EmailField(label="E-mail")
    matricula = forms.CharField(label="Matrícula", max_length=20)
    telefone = forms.CharField(label="Telefone", max_length=15, required=False)
    senha = forms.CharField(label="Senha", widget=forms.PasswordInput)
    confirmar_senha = forms.CharField(label="Confirmar Senha", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['first_name', 'email']

    def clean_matricula(self):
        mat = self.cleaned_data.get('matricula')
        if User.objects.filter(username=mat).exists():
            raise forms.ValidationError("Esta matrícula já está registada.")
        return mat

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("senha") != cleaned_data.get("confirmar_senha"):
            raise forms.ValidationError("As senhas não coincidem.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["matricula"] # Matricula vira o login
        user.set_password(self.cleaned_data["senha"])
        if commit:
            user.save()
            # Atualiza o perfil criado pelo Signal
            perfil = user.perfil
            perfil.matricula = self.cleaned_data.get('matricula')
            perfil.telefone = self.cleaned_data.get('telefone')
            perfil.save()
        return user
    

class LoginForm(AuthenticationForm):
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username:
            # 1. Verifica se o usuário existe e está inativo INDEPENDENTE da senha
            user_query = User.objects.filter(username=username)
            if user_query.exists():
                user = user_query.first()
                if not user.is_active:
                    raise forms.ValidationError(
                        "Sua conta ainda não foi aprovada pelo administrador. "
                        "Você receberá um e-mail quando o acesso for liberado."
                    )
                
        return super().clean()