from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator # Importe o validador de Regex

class RegistroForm(forms.ModelForm):
    # Criamos o validador que aceita apenas números (\d+)
    apenas_numeros = RegexValidator(
        regex=r'^\d+$',
        message='A matrícula deve conter apenas números.'
    )

    # Sobrescrevemos o campo username para aplicar o validador e mudar o label
    username = forms.CharField(
        label="Matrícula",
        validators=[apenas_numeros],
        help_text=None # Remove aquele texto de "150 caracteres..."
    )

    senha = forms.CharField(widget=forms.PasswordInput, label="Senha")
    confirmar_senha = forms.CharField(widget=forms.PasswordInput, label="Confirme a Senha")
    first_name = forms.CharField(label="Nome Completo", required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email']
        labels = {
            'first_name': 'Nome Completo',
            'email': 'E-mail',
        }

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get("senha")
        confirmar_senha = cleaned_data.get("confirmar_senha")

        if senha != confirmar_senha:
            raise ValidationError("As senhas não conferem.")
        return cleaned_data