import os
from unittest.mock import patch

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import Perfil


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
)
class AccountFlowTests(TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(
            os.environ,
            {
                'EMAIL_HOST_USER': 'noreply@example.com',
                'EMAIL_HOST_PASSWORD': 'dummy-password',
            },
            clear=False,
        )
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    def test_register_creates_pending_email_status(self):
        response = self.client.post(
            reverse('register'),
            {
                'first_name': 'Maria Teste',
                'email': 'maria@example.com',
                'matricula': '2026001',
                'telefone': '88999999999',
                'senha': 'SenhaSegura123',
                'confirmar_senha': 'SenhaSegura123',
            },
        )

        user = User.objects.get(username='2026001')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(user.is_active)
        self.assertEqual(user.perfil.status, Perfil.STATUS_PENDENTE_EMAIL)
        self.assertEqual(len(mail.outbox), 1)

    def test_activation_moves_user_to_pending_approval_once(self):
        user = User.objects.create_user(
            username='2026002',
            email='joao@example.com',
            password='SenhaSegura123',
            first_name='Joao',
            is_active=False,
        )
        user.perfil.status = Perfil.STATUS_PENDENTE_EMAIL
        user.perfil.matricula = '2026002'
        user.perfil.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        activation_url = reverse('activate_account', kwargs={'uidb64': uid, 'token': token})

        first_response = self.client.get(activation_url)
        user.refresh_from_db()

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(user.perfil.status, Perfil.STATUS_PENDENTE_APROVACAO)
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)

        second_response = self.client.get(activation_url)
        user.refresh_from_db()

        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(user.perfil.status, Perfil.STATUS_PENDENTE_APROVACAO)
        self.assertEqual(len(mail.outbox), 1)

    def test_login_message_for_pending_email(self):
        user = User.objects.create_user(
            username='2026003',
            email='ana@example.com',
            password='SenhaSegura123',
            first_name='Ana',
            is_active=False,
        )
        user.perfil.status = Perfil.STATUS_PENDENTE_EMAIL
        user.perfil.matricula = '2026003'
        user.perfil.save()

        response = self.client.post(
            reverse('login'),
            {'username': '2026003', 'password': 'SenhaSegura123'},
        )

        self.assertContains(response, 'Confirme seu e-mail antes de entrar no sistema.')

    def test_login_message_for_pending_approval(self):
        user = User.objects.create_user(
            username='2026004',
            email='carlos@example.com',
            password='SenhaSegura123',
            first_name='Carlos',
            is_active=False,
        )
        user.perfil.status = Perfil.STATUS_PENDENTE_APROVACAO
        user.perfil.matricula = '2026004'
        user.perfil.save()

        response = self.client.post(
            reverse('login'),
            {'username': '2026004', 'password': 'SenhaSegura123'},
        )

        self.assertContains(response, 'Sua conta ainda não foi aprovada pelo administrador.')
