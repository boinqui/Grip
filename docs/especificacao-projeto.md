# BACHARELADO EM SISTEMAS DE INFORMAÇÃO
## ESPECIFICAÇÃO DE PROJETO — 2026

**Carla Ferraz de Araujo | Eduardo Baccon Bertol | Lucas Dal Pra Brascher**

---

## SUMÁRIO

1. [Artefato 1 — Quadro "3 Objetivos"](#artefato-1)
2. [Artefato 2 — Quadro "É – Não É – Faz – Não Faz"](#artefato-2)
3. [Artefato 3 — Relação de Atores e Requisitos](#artefato-3)
4. [Artefato 4 — Modelo Relacional](#artefato-4)

---

## ARTEFATO 1 — Quadro "3 Objetivos" {#artefato-1}

**NOME DO PRODUTO:** GRIP

| # | Objetivo | Descrição |
|---|----------|-----------|
| 1 | Gestão digital centralizada | Centralizar o cadastro de alunos, professores e aulas, substituindo controles manuais por gestão digital. |
| 2 | Acesso por perfil | Adaptar o acesso por perfil, com jornadas distintas e personalizadas para alunos e professores no mesmo sistema. |
| 3 | Acessibilidade total | Substituir papéis e anotações por uma gestão centralizada da escola, acessível de qualquer dispositivo. |

---

## ARTEFATO 2 — Quadro "É – Não É – Faz – Não Faz" {#artefato-2}

**NOME DO PRODUTO:** GRIP

| É | Não é |
|---|-------|
| Plataforma web para gestão de aulas de ballet | Rede social |
| Sistema de agendamento de aulas ao vivo | E-commerce de produtos físicos |
| Gestão de cadastro de alunos e professores | Sistema de controle financeiro completo |
| | Plataforma de aulas gravadas |

| Faz | Não faz |
|-----|---------|
| Permite contratação de planos de aulas | Não cria planos personalizados com IA |
| Permite agendamento de aulas ao vivo com professores | Não possui funcionalidades sociais (feed, comentários, seguidores) |
| Gerencia agenda básica de aulas ao vivo | Não realiza gestão financeira avançada para professores |
| | Não oferece correção automática de movimentos (computer vision) |
| | Não substitui acompanhamento pedagógico individual contínuo |

---

## ARTEFATO 3 — Relação de Atores e Requisitos {#artefato-3}

### Atores

| # | Ator | Descrição |
|---|------|-----------|
| Usu 1 | **Administrador** | Faz a gestão dos dados e das funcionalidades do sistema |
| Usu 2 | **Aluno** | Acessa o sistema, agenda aulas online e contrata professores/planos |

---

### Requisitos Não Funcionais

| # | Requisito | Sprint | Usuário | Status |
|---|-----------|:------:|---------|:------:|
| **RNF1** | Criar interface user-friendly (CSS + HTML + JS) e responsiva para todas as telas do sistema | 1 | N/A | ✅ Feito |
| **RNF2** | Validar campos de entrada (RegEx e/ou Javascript) em todos os formulários | 1 | N/A | ✅ Feito |
| **RNF3** | Persistir em BD Relacional todos os dados do sistema | 1 | N/A | ✅ Feito |
| **RNF4** | Autenticação de usuário com senha criptografada, mantida no BD | 1 | N/A | ✅ Feito |
| **RNF5** | Identificar, em todas as interfaces, o usuário que estiver autenticado | 1 | N/A | ✅ Feito |
| **RNF6** | Controlar e gerenciar sessão com os dados do usuário | 2 | Adm, Usuário | 🔄 A Fazer |
| **RNF7** | Exigir autenticação, caso o usuário acesse uma URL da aplicação quando não estiver autenticado | 2 | Adm, Usuário | 🔄 A Fazer |
| **RNF8** | Expirar a sessão do usuário após timeout | 2 | Adm, Usuário | ✅ Feito |
| **RNF9** | Fazer upload da imagem do avatar do usuário autenticado para o servidor | 2 | Adm, Usuário | 🔄 A Fazer |
| **RNF10** | Criação de filtros de pesquisa para as informações do sistema (Aulas, Professores) | 2 | Adm, Usuário | 🔄 A Fazer |

---

### Requisitos Funcionais

| # | Requisito | Sprint | Usuário | Status |
|---|-----------|:------:|---------|:------:|
| **RF1** | Gerenciar Cadastro de Alunos (CRUD) | 1 | Adm, Usuário | ✅ Feito |
| **RF2** | Gerenciar Cadastro de Professores (CRUD) | 1 | Adm | ✅ Feito |
| **RF3** | Gerenciar Cadastro de Aulas (CRUD) | 1 | Adm | ✅ Feito |
| **RF4** | Gerenciar Cadastro de Movimentos (CRUD) | 2 | Adm | 🔄 A Fazer |
| **RF5** | Agendar aula online de ballet | 2 | Usuário | 🔄 Em andamento |
| **RF6** | Contratar professor de ballet | 2 | Usuário | 🔄 A Fazer |
| **RF7** | Contratar um plano de ballet | 2 | Usuário | 🔄 A Fazer |

> **Nota sobre RF5:** Parcialmente implementado no backend (rota `/agendar-aula`). Listado no Trello como "FUNCIONALIDADE EXTRA — arrumar a parte de agendar aula".

---

### Resumo por Sprint

#### Sprint 1 — ✅ Concluída

| Card Trello | Tipo | Entregável |
|-------------|------|-----------|
| Preparar Ambiente Web | — | Servidor FastAPI + BD MySQL configurados |
| Design Tela Home | RNF1 | Layout e CSS da Home |
| Design Tela de Login | RNF1 | Layout e CSS do Login |
| Design Tela de Cadastro | RNF1 | Layout e CSS do Cadastro |
| Implementação Tela Login — Código | RNF4 | Rota de autenticação |
| Implementação Tela Cadastro — Código | RF1 | Rota de cadastro de aluno |
| Implementação Código Tela Home | RNF1 | Renderização da home |
| Modelagem Banco de Dados | RNF3 | Schema SQL (`bd_grip.sql`) |
| RNF1 — Criar interface user-friendly | RNF1 | CSS global + responsividade |
| RNF2 — Validar campos de entrada | RNF2 | Validators (RegEx + JS) |
| RNF3 — Persistir em BD Relacional | RNF3 | Integração PyMySQL |
| RNF4 — Autenticação senha criptografada | RNF4 | PBKDF2-SHA256 + salt |
| RNF5 — Identificar usuário autenticado | RNF5 | Navbar com nome + logout |
| RF1 — Gerenciar Cadastro de Alunos | RF1 | CRUD completo de alunos |
| RF2 — Gerenciar Cadastro de Professores | RF2 | CRUD completo de professores |
| RF3 — Gerenciar Cadastro de Aulas | RF3 | CRUD completo de aulas |
| Template Modal (Front) | RNF2 | Modal de mensagens padronizado |
| Página Sobre | RNF1 | Tela estática |
| Página Aulas | RNF1 | Tela estática |
| Página Professores | RNF1 | Listagem de professores |
| Página Perfil Professor | RNF1 | Perfil público do professor |
| Página Perfil Aluno | RNF1 | Dashboard do aluno |
| Página Perfil Admin | RNF1 + RNF5 | Dashboard do admin |
| Validação de rotas exclusivas do admin | RNF7 | `verify_admin()` + `verify_logged_in()` |
| Adicionar olho na senha | RNF2 | Toggle visibilidade de senha |
| Inserir campo idade | RF1 | Campo `data_nascimento` no cadastro |
| Refatorar CSS | RNF1 | Padronização visual |
| RNF8 — Expirar sessão após timeout | RNF8 | `max_age=3600` no SessionMiddleware |

#### Sprint 2 — 🔄 Em Andamento

| Card Trello | Tipo | Status |
|-------------|------|--------|
| RNF6 — Controlar e gerenciar sessão | RNF6 | 🔄 A Fazer |
| RNF7 — Exigir autenticação para URLs protegidas | RNF7 | 🔄 A Fazer |
| RNF9 — Upload imagem do avatar | RNF9 | 🔄 A Fazer |
| RNF10 — Inserir Filtro (Aulas, Professores) | RNF10 | 🔄 A Fazer |
| RF5 — Agendar aula online | RF5 | 🔄 Em andamento |
| Verificar responsividade em todas as telas | RNF1 | 🔄 A Fazer |
| Verificar campos de todos os formulários | RNF2 | 🔄 A Fazer |
| Adicionar imagens no banco | RNF9 | 🔄 A Fazer |
| Corrigir path das imagens | RNF9 | 🔄 A Fazer |
| Atualizar foto professor | RNF9 | 🔄 A Fazer |
| Avisos de feedback sem alert JS | RNF2 | 🔄 A Fazer |
| Modal ao criar conta | RNF2 | 🔄 A Fazer |
| Redirecionar para perfil após cadastro | RF1 | 🔄 A Fazer |
| Arrumar professores-perfil com banco | RF2 | 🔄 A Fazer |
| Exibir primeiro nome do usuário no botão | RNF5 | 🔄 A Fazer |
| Corrigir alert JS ao remover aula/aluno | RNF2 | 🔄 A Fazer |

---

## ARTEFATO 4 — Modelo Relacional {#artefato-4}

Modelos disponíveis na pasta `modelos_brmodelo/` do repositório:

- `ModeloConceitual.brM3` — Diagrama Entidade-Relacionamento (DER)
- `ModeloLogico.brM3` — Modelo Lógico Relacional (engenharia reversa)

**Tabelas implementadas:**

```
Professor (id, nome, registro_drt, cpf, email, senha, fotoPerfil)
Aluno (id, nome, cpf, telefone, email, senha, data_nascimento, fotoPerfil)
Aula (id, nome, data, descricao, fk_Professor_id)
Professor_Aluno (fk_Professor_id, fk_Aluno_id)
Agendamento_Aula (id, fk_Aluno_id, fk_Professor_id, tipo_aula, data_hora, observacao, status, criado_em)
```

---

## REFERÊNCIAS BIBLIOGRÁFICAS

SCHWABER, K.; SUTHERLAND, J. **Guia do SCRUM — o guia definitivo para o Scrum: as regras do jogo.** 2020.
