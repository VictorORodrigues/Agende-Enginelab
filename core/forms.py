from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinLengthValidator

class RegistroForm(forms.ModelForm):
    apenas_numeros = RegexValidator(
        regex=r'^\d+$',
        message='A matrícula deve conter apenas números.'
    )

    # Definindo o campo com a mensagem de erro única personalizada
    username = forms.CharField(
        label="Matrícula",
        validators=[apenas_numeros],
        help_text=None,
        error_messages={
            'unique': "Um usuário com esta matrícula já existe."
        }
    )

    senha = forms.CharField(
        widget=forms.PasswordInput, 
        label="Senha",
        validators=[MinLengthValidator(6, message="A senha deve ter pelo menos 6 caracteres.")]
    )
    
    confirmar_senha = forms.CharField(
        widget=forms.PasswordInput, 
        label="Confirme a Senha"
    )
    
    first_name = forms.CharField(label="Nome Completo", required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email']
        labels = {
            'first_name': 'Nome Completo',
            'email': 'E-mail',
        }
        # Você pode manter ou remover o error_messages daqui, 
        # mas o definido acima no campo tem prioridade.

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este e-mail já está cadastrado no sistema.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get("senha")
        confirmar_senha = cleaned_data.get("confirmar_senha")

        if senha and confirmar_senha and senha != confirmar_senha:
            raise ValidationError("As senhas não conferem.")
        return cleaned_data