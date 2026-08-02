from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db.utils import OperationalError
from django.db import IntegrityError
from .models import Perfil, Setor
from .security import get_client_ip, is_locked, failure_counts, register_failure, register_success, limits

class SetorForm(forms.ModelForm):
    class Meta:
        model = Setor
        fields = ['nome', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'maxlength': '100', 'placeholder': 'Ex: Laboratório de Hardware'}),
            'descricao': forms.Textarea(attrs={'maxlength': '500', 'rows': 3, 'placeholder': 'Descrição breve do setor...'}),
        }

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

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError("Este e-mail já está registado.")
        return email

    def clean_matricula(self):
        mat = self.cleaned_data.get('matricula')
        mat = (mat or '').strip()
        try:
            if User.objects.filter(username__iexact=mat).exists():
                raise forms.ValidationError("Esta matrícula já está registada.")
            if Perfil.objects.filter(matricula__iexact=mat).exists():
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
    email = forms.EmailField(label='E-mail')

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._instance = instance
        self.setores_list = Setor.objects.all().order_by('nome')

        # Adiciona campos dinâmicos para cada setor
        for setor in self.setores_list:
            field_name_itens = f'pode_itens_{setor.id}'
            field_name_emprestimos = f'pode_emprestimos_{setor.id}'

            self.fields[field_name_itens] = forms.BooleanField(required=False, label="Itens")
            self.fields[field_name_emprestimos] = forms.BooleanField(required=False, label="Empréstimos")

            if instance:
                self.fields['email'].initial = instance.user.email
                from .models import JurisdicaoSubAdmin
                jur = JurisdicaoSubAdmin.objects.filter(subadmin=instance, setor=setor).first()
                if jur:
                    self.fields[field_name_itens].initial = jur.pode_gerenciar_itens
                    self.fields[field_name_emprestimos].initial = jur.pode_gerenciar_emprestimos

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()
            # Verifica se já existe um usuário com esse email que JÁ SEJA subadmin
            user_existente = User.objects.filter(email__iexact=email).first()
            if user_existente:
                perfil = getattr(user_existente, 'perfil', None)
                if perfil and perfil.eh_subadm:
                    if not self._instance or self._instance.user.pk != user_existente.pk:
                        raise forms.ValidationError("Este e-mail já pertence a um Sub-Administrador.")
        return email

    def save(self):
        from django.db import transaction
        from django.contrib.auth.models import User as AuthUser
        from .models import Perfil as PerfilModel, JurisdicaoSubAdmin
        import secrets
        import string

        email = self.cleaned_data['email']
        criado = False

        with transaction.atomic():
            user = AuthUser.objects.filter(email__iexact=email).first()

            if self._instance:
                user = self._instance.user
                user.email = email
                user.username = email
                user.save()
                perfil = self._instance
                perfil.jurisdicoes.all().delete()
                criado = False
            elif user:
                perfil = user.perfil
                perfil.tipo = 'SUBADM'
                perfil.status = PerfilModel.STATUS_APROVADO
                perfil.save()
                perfil.jurisdicoes.all().delete()
                criado = False
            else:
                random_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(20))
                user = AuthUser.objects.create_user(
                    username=email,
                    email=email,
                    password=random_password,
                    is_active=False,
                )
                perfil = user.perfil
                perfil.tipo = 'SUBADM'
                perfil.status = PerfilModel.STATUS_PENDENTE
                perfil.save()
                criado = True

            for setor in Setor.objects.all():
                pode_itens = self.cleaned_data.get(f'pode_itens_{setor.id}')
                pode_emp = self.cleaned_data.get(f'pode_emprestimos_{setor.id}')

                if pode_itens or pode_emp:
                    JurisdicaoSubAdmin.objects.create(
                        subadmin=perfil,
                        setor=setor,
                        pode_gerenciar_itens=bool(pode_itens),
                        pode_gerenciar_emprestimos=bool(pode_emp)
                    )
        return perfil, criado


class CompleteSubAdminProfileForm(forms.Form):
    nome_completo = forms.CharField(label="Nome Completo", max_length=150)
    telefone = forms.CharField(label="Telefone", max_length=15)
    senha = forms.CharField(label="Nova Senha", widget=forms.PasswordInput)
    confirmar_senha = forms.CharField(label="Confirmar Senha", widget=forms.PasswordInput)

    def clean_senha(self):
        senha = self.cleaned_data.get("senha")
        if senha:
            validate_password(senha)
        return senha

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get("senha")
        confirmar_senha = cleaned_data.get("confirmar_senha")
        if senha and confirmar_senha and senha != confirmar_senha:
            raise forms.ValidationError("As senhas não coincidem.")
        return cleaned_data


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
                from django.db.models import Q
                user = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username))
                if user.count() > 1:
                    user = user.filter(is_active=True).first() or user.first()
                else:
                    user = user.first()

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
