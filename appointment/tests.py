from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from account.models import Perfil


class AppointmentDashboardVisibilityTests(TestCase):
    def _make_user(self, username: str, tipo: str) -> User:
        user = User.objects.create_user(username=username, password='test-pass-123')
        perfil = user.perfil
        perfil.tipo = tipo
        perfil.status = Perfil.STATUS_ATIVO
        perfil.matricula = username
        perfil.save()
        user.refresh_from_db()
        return user

    def test_dashboard_student_sees_student_section(self):
        user = self._make_user('20260001', 'ALUNO')
        self.client.force_login(user)

        response = self.client.get(reverse('appointment:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'appointment/dashboard.html')
        self.assertContains(response, 'Área do aluno')
        self.assertNotContains(response, 'Área do subadministrador')
        self.assertNotContains(response, 'Área do administrador geral')

    def test_dashboard_subadm_sees_subadm_section(self):
        user = self._make_user('20260002', 'SUBADM')
        self.client.force_login(user)

        response = self.client.get(reverse('appointment:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Área do subadministrador')
        self.assertNotContains(response, 'Área do administrador geral')

    def test_dashboard_admin_sees_subadm_and_admin_sections(self):
        user = self._make_user('20260003', 'ADMIN')
        self.client.force_login(user)

        response = self.client.get(reverse('appointment:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Área do subadministrador')
        self.assertContains(response, 'Área do administrador geral')
