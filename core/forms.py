from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class RegistroForm(forms.ModelForm):
    senha = forms.CharField(widget=forms.PasswordInput, label="Senha")
    confirmar_senha = forms.CharField(widget=forms.PasswordInput, label="Confirme a Senha")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        help_texts = {'username': 'Use sua matrícula ou nome de usuário.'}

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not (email.endswith('@ufc.br') or email.endswith('@alu.ufc.br')):
            raise ValidationError("Somente e-mails institucionais da UFC são permitidos.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get("senha")
        confirmar_senha = cleaned_data.get("confirmar_senha")

        if senha != confirmar_senha:
            raise ValidationError("As senhas não conferem.")