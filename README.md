# Agende EngineLab UFC

Sistema de gestão para o laboratório EngineLab UFC: controle de empréstimo de itens (equipamentos, notebooks, livros) por setor, com aprovação por administradores/sub-administradores, renovação, notificações por e-mail e controle de permissões por setor.

## Objetivos

- Centralizar o controle de empréstimo de itens do laboratório (equipamentos, notebooks, livros), substituindo controle manual/planilhas.
- Organizar o acervo por setores, com permissões específicas para quem pode gerenciar cada um.
- Formalizar o fluxo de solicitação → aprovação → devolução/renovação de empréstimos, com histórico rastreável.
- Delegar a administração a sub-administradores por setor, mantendo controle centralizado para administradores gerais.
- Reduzir atrasos e esquecimentos por meio de notificações automáticas por e-mail (itens atrasados, devoluções do dia, novos cadastros/solicitações pendentes).
- Manter o acesso seguro, com aprovação de novos cadastros e proteção contra força bruta no login.

## Stack

- Python / Django 6
- PostgreSQL (produção) ou SQLite (desenvolvimento local)
- Sem frontend framework — templates Django + CSS puro

## Requisitos

- Python 3.12+
- pip
- Docker (opcional, só se for usar Postgres localmente em vez de SQLite)

## 1. Clonar e criar o ambiente virtual

```bash
git clone https://github.com/VictorORodrigues/Agende-Enginelab.git
cd Agende-Enginelab
python -m venv .venv
```

Ativar o ambiente virtual:

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
```

Instalar as dependências:

```bash
pip install -r requirements.txt
```

## 2. Configurar variáveis de ambiente

Copie o arquivo de exemplo e preencha com valores próprios:

```bash
cp .env.example .env
```

| Variável | Descrição |
|---|---|
| `DEBUG` | `true` em desenvolvimento, `false` em produção |
| `SECRET_KEY` | Gere uma chave própria (nunca reutilize a de outro ambiente) |
| `ALLOWED_HOSTS` | Domínios/IPs permitidos, separados por vírgula |
| `DB_ENGINE` | `django.db.backends.postgresql` ou `django.db.backends.sqlite3` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Credenciais do Postgres (ignoradas se usar SQLite) |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Conta de e-mail usada para enviar notificações (recomendado: uma [senha de app do Gmail](https://myaccount.google.com/apppasswords), não a senha normal da conta) |
| `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` | Deixe `false` em desenvolvimento; `true` em produção com HTTPS |
| `ACCOUNT_MAX_FAILED_LOGINS_PER_MINUTE`, `ACCOUNT_LOCKOUT_THRESHOLD`, `ACCOUNT_LOCKOUT_SECONDS`, `ACCOUNT_CAPTCHA_AFTER_FAILS` | Proteção contra força bruta no login |

Para rodar rápido em desenvolvimento sem precisar de Postgres, deixe `DB_ENGINE` em branco no `.env` — o sistema cai automaticamente para SQLite (`db.sqlite3`) quando `DEBUG=true`.

Duas variáveis opcionais, não presentes no `.env.example`, mas aceitas caso queira customizar:
- `EMAIL_ADMIN_LAB` — para onde vão os avisos de "novo cadastro"/"novo empréstimo pendente" (padrão: o próprio `EMAIL_HOST_USER`)
- `DEFAULT_FROM_EMAIL` — remetente exibido nos e-mails (padrão: `EngineLab UFC <EMAIL_HOST_USER>`)

### Banco de dados com Postgres (opcional)

Se preferir Postgres em vez de SQLite, suba o container incluso:

```bash
docker-compose up -d
```

E preencha `DB_NAME`, `DB_USER`, `DB_PASSWORD` no `.env` com os mesmos valores do `docker-compose.yml`.

## 3. Migrations e usuário administrador

```bash
python manage.py migrate
python manage.py createsuperuser
```

`createsuperuser` só dá acesso ao painel `/admin/` do Django — ele **não** torna o usuário administrador do sistema (isso é um papel à parte, controlado por `Perfil.tipo`). Para o primeiro usuário virar administrador do sistema, rode:

```bash
python manage.py shell -c "
from django.contrib.auth import get_user_model
from account.models import Perfil
u = get_user_model().objects.get(username='SEU_USUARIO_AQUI')
Perfil.objects.filter(user=u).update(tipo='ADMIN')
"
```

A partir daí ele consegue acessar `/account/admin/...` e promover outros usuários pela própria interface. Usuários cadastrados pelo formulário público (`/registro/`) ficam pendentes até um administrador aprovar.

## 4. Rodar o servidor

```bash
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/`.

## Notificações automáticas por e-mail

Dois comandos devem ser agendados (cron, Task Scheduler, etc.) para rodar diariamente:

```bash
python manage.py notificar_atrasos       # avisa quem está com item atrasado
python manage.py notificar_devolucoes    # avisa quem devolve hoje + resumo pro admin
```

## Estrutura do projeto

- `account/` — autenticação, perfis (aluno / sub-admin / admin), setores, permissões
- `catalog/` — itens, categorias, empréstimos (solicitação, aprovação, devolução, renovação)
- `agende_enginelab/` — configurações do projeto (settings, urls)

## Papéis de usuário

- **Aluno**: solicita empréstimos, acompanha status, renova.
- **Sub-Administrador**: gerencia itens/empréstimos apenas dos setores sob sua jurisdição (definida pelo admin).
- **Administrador**: acesso total — usuários, sub-admins, setores, itens, empréstimos.
