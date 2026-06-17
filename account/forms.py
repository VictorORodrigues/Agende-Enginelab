from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db.utils import OperationalError
from django.db import IntegrityError
from .models import Perfil
from .security import get_client_ip, is_locked, failure_counts, register_failure, register_success, limits

class RegisterForm(forms.ModelForm):
    first_name = forms.CharField(label="Nome Completo", max_length=150)
    email = forms.EmailField(label="E-mail")
    matricula = forms.CharField(
        label="Matrícula",
        max_length=20,
        validators=[RegexValidator(regex=r'^\d+$', message="A matrícula deve conter apenas números.")],
    )
    telefone = forms.CharField(label="Telefone", max_length=15, required=False)
    senha = forms.CharField(label="Senha", widget=forms.PasswordInput)
    confirmar_senha = forms.CharField(label="Confirmar Senha", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['first_name', 'email']

    def clean_matricula(self):
        mat = self.cleaned_data.get('matricula')
        mat = (mat or '').strip()
        try:
            if User.objects.filter(username=mat).exists():
                raise forms.ValidationError("Esta matrícula já está registada.")
            if Perfil.objects.filter(matricula=mat).exists():
                raise forms.ValidationError("Esta matrícula já está registada.")
        except OperationalError:
            raise forms.ValidationError("Banco de dados não inicializado. Execute as migrações (manage.py migrate).")
        return mat

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get("senha")
        confirmar_senha = cleaned_data.get("confirmar_senha")

        # So compara as senhas quando ambas passaram pela validacao individual.
        if senha and confirmar_senha and senha != confirmar_senha:
            raise forms.ValidationError("As senhas não coincidem.")
        return cleaned_data

    def clean_senha(self):
        senha = self.cleaned_data.get("senha")
        if senha:
            validate_password(senha, user=None)
        return senha

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["matricula"] # Matricula vira o login
        user.set_password(self.cleaned_data["senha"])
        user.is_active = False
        if commit:
            try:
                user.save()
                perfil = user.perfil
                perfil.status = Perfil.STATUS_PENDENTE
                perfil.matricula = self.cleaned_data.get('matricula')
                perfil.telefone = self.cleaned_data.get('telefone')
                perfil.save()
            except IntegrityError:
                raise forms.ValidationError("Esta matrícula já está registada.")
        return user
    

class SubAdminForm(forms.Form):
    nome = forms.CharField(label='Nome completo', max_length=150)
    email = forms.EmailField(label='E-mail')
    matricula = forms.CharField(label='Matrícula', max_length=20)
    senha = forms.CharField(label='Senha', widget=forms.PasswordInput, required=False)
    escopo_agendamento = forms.BooleanField(label='Agendamentos', required=False)
    escopo_equipamento = forms.BooleanField(label='Equipamentos', required=False)
    escopo_livro = forms.BooleanField(label='Livros', required=False)
    escopo_emprestimo = forms.BooleanField(label='Empréstimos', required=False)

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._instance = instance
        if instance:
            self.fields['nome'].initial = instance.user.get_full_name()
            self.fields['email'].initial = instance.user.email
            self.fields['matricula'].initial = instance.matricula
            escopos_ativos = set(instance.permissoes.values_list('escopo', flat=True))
            from .models import PermissaoSubAdmin as PAD
            self.fields['escopo_equipamento'].initial = PAD.ESCOPO_EQUIPAMENTO in escopos_ativos
            self.fields['escopo_livro'].initial = PAD.ESCOPO_LIVRO in escopos_ativos
            self.fields['escopo_agendamento'].initial = PAD.ESCOPO_AGENDAMENTO in escopos_ativos
            self.fields['escopo_emprestimo'].initial = PAD.ESCOPO_EMPRESTIMO in escopos_ativos

    def clean_senha(self):
        senha = self.cleaned_data.get('senha')
        if senha:
            validate_password(senha)
        elif not self._instance:
            raise forms.ValidationError('Senha obrigatória para novos SubAdmins.')
        return senha

    def save(self):
        from django.db import transaction
        from django.contrib.auth.models import User as AuthUser
        from .models import Perfil as PerfilModel, PermissaoSubAdmin as PAD
        nome = self.cleaned_data['nome']
        email = self.cleaned_data['email']
        matricula = self.cleaned_data['matricula']
        senha = self.cleaned_data.get('senha')
        partes = nome.strip().split(' ', 1)
        first_name = partes[0]
        last_name = partes[1] if len(partes) > 1 else ''

        with transaction.atomic():
            if self._instance:
                user = self._instance.user
                user.first_name = first_name
                user.last_name = last_name
                user.email = email
                if senha:
                    user.set_password(senha)
                user.save()
                perfil = self._instance
                perfil.matricula = matricula
                perfil.save()
                perfil.permissoes.all().delete()
            else:
                user = AuthUser.objects.create_user(
                    username=matricula,
                    email=email,
                    password=senha,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                )
                perfil = user.perfil
                perfil.tipo = 'SUBADM'
                perfil.status = PerfilModel.STATUS_APROVADO
                perfil.matricula = matricula
                perfil.save()

            mapa = {
                'escopo_equipamento': PAD.ESCOPO_EQUIPAMENTO,
                'escopo_livro': PAD.ESCOPO_LIVRO,
                'escopo_agendamento': PAD.ESCOPO_AGENDAMENTO,
                'escopo_emprestimo': PAD.ESCOPO_EMPRESTIMO,
            }
            for campo, escopo in mapa.items():
                if self.cleaned_data.get(campo):
                    PAD.objects.get_or_create(subadmin=perfil, escopo=escopo)
        return perfil


class LoginForm(AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "autocomplete": "username"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "form-control", "autocomplete": "current-password"}
        )

        username = (self.data.get("username") or "").strip()
        ip = get_client_ip(request)
        if username and ip:
            per_minute, consecutive = failure_counts(ip, username)
            if consecutive >= limits()["captcha_after"] and "captcha_answer" not in self.fields:
                self.fields["captcha_answer"] = forms.IntegerField(
                    label="Confirme que você não é um robô: quanto é 2 + 3?",
                    required=True,
                )
                self.fields["captcha_answer"].widget.attrs.update({"class": "form-control"})

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        ip = get_client_ip(self.request)

        if username and ip and is_locked(ip, username):
            raise forms.ValidationError("Muitas tentativas. Tente novamente mais tarde.")

        if "captcha_answer" in self.fields:
            captcha_answer = self.cleaned_data.get("captcha_answer")
            if captcha_answer != 5:
                if username and ip:
                    register_failure(ip, username)
                raise forms.ValidationError("Verificação inválida. Tente novamente.")

        if username and password:
            try:
                user = User.objects.filter(username=username).first()
                if user and user.check_password(password) and not user.is_active:
                    status = getattr(user.perfil, 'status', Perfil.STATUS_PENDENTE)
                    if status == Perfil.STATUS_PENDENTE:
                        raise forms.ValidationError(
                            "Seu cadastro ainda não foi aprovado pelo administrador. "
                            "Você receberá um e-mail quando o acesso for liberado."
                        )
                    if status == Perfil.STATUS_REJEITADO:
                        raise forms.ValidationError(
                            "Seu cadastro não foi aprovado. "
                            "Entre em contato com a administração do laboratório."
                        )
            except OperationalError:
                raise forms.ValidationError("Banco de dados não inicializado. Execute as migrações (manage.py migrate).")

        try:
            cleaned = super().clean()
        except forms.ValidationError:
            if username and ip:
                register_failure(ip, username)
            raise
        except OperationalError:
            raise forms.ValidationError("Banco de dados não inicializado. Execute as migrações (manage.py migrate).")

        if username and ip:
            register_success(ip, username)
        return cleaned
