# Design: Dashboard Unico No App Appointment (Com Extras Para Subadm/Admin)

## Objetivo

Ter uma unica tela inicial do sistema de agendamentos (dashboard) para todos os perfis, mantendo:

- base comum para todos
- blocos extras visiveis para `SUBADM`
- blocos extras adicionais visiveis para `ADMIN` (admin inclui tudo do subadm + extras)

## Contexto Atual

- A rota `appointment:home` renderiza templates diferentes por perfil em [views.py](file:///c:/Users/victo/OneDrive/Documentos/C%C3%B3digos/agende_enginelab/appointment/views.py#L7-L14)
- Os templates `student/subadm/admin` estao vazios.

## Escopo

Inclui:

- dashboard unico (uma unica view + um unico template)
- modularizacao do template por partials (widgets)
- guardas de permissao para endpoints futuros (nao depender apenas de esconder botoes)
- limpeza/organizacao dos templates vazios do `appointment`

Nao inclui:

- implementacao completa das funcionalidades de agendamento (CRUD, disponibilidade, etc.)
- refatoracao completa do projeto inteiro

## Decisoes Confirmadas

- Um unico dashboard (opcao A)
- Admin ve tudo do subadm + extras (opcao 1)

## Arquitetura Proposta

### View unica

- Manter uma unica rota: `GET /appointment/` (nome `appointment:home`)
- A view monta um contexto comum (ex.: proximos agendamentos, avisos, etc.)
- A view expõe flags para o template:
  - `is_student`, `is_subadm`, `is_admin`

### Templates modularizados (partials)

Criar um template principal:

- `appointment/templates/appointment/dashboard.html`

E partials:

- `appointment/templates/appointment/partials/_common.html` (sempre)
- `appointment/templates/appointment/partials/_student.html` (apenas aluno)
- `appointment/templates/appointment/partials/_subadm.html` (subadm e admin)
- `appointment/templates/appointment/partials/_admin.html` (apenas admin)

Regras de inclusao:

- `is_subadm` deve ser verdadeiro para `SUBADM` e `ADMIN`
- `is_admin` apenas para `ADMIN`

## Permissoes (Importante)

O fato do botao/aba nao aparecer no dashboard nao e permissao.

Para cada endpoint de acao sensivel (ex.: aprovar emprestimo, cadastrar equipamento, gerenciar setores), a view deve validar:

- usuario autenticado
- status da conta ativo (via `User.is_active`)
- perfil adequado (ex.: `request.user.perfil.eh_subadm` ou `eh_admin`)

Preferencia:

- usar decorators utilitarios locais (ex.: `@require_subadm`, `@require_admin`) para evitar duplicacao.

## Organizacao De Pastas (Appointment)

Curto prazo:

- manter `appointment/views.py` pequeno e focado no dashboard
- colocar apenas templates do app em `appointment/templates/appointment/...`

Medio prazo (quando crescer):

- `appointment/selectors.py` (consultas ORM)
- `appointment/services.py` (regras de negocio)
- `appointment/permissions.py` (decorators e checagens)
- `appointment/views/` (split em modulos por area)

## Migracao De Templates Existentes

- Remover os templates vazios atuais:
  - `appointment/templates/student/studant_home.html`
  - `appointment/templates/subadm/subadm_home.html`
  - `appointment/templates/admin/admin_home.html`
- Substituir por `dashboard.html` + partials.

## Criterios De Sucesso

- Todos os perfis entram em `/appointment/` e veem a mesma estrutura base
- `SUBADM` ve os blocos extras de subadm
- `ADMIN` ve os blocos extras de subadm + os extras de admin
- Nenhum endpoint privilegiado pode ser acessado por aluno apenas "chamando a URL"

## Testes Minimos

- teste de view: aluno renderiza dashboard e nao ve blocos de subadm/admin
- teste de view: subadm ve bloco de subadm
- teste de view: admin ve bloco de subadm e admin
