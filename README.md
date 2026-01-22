# 🎯 Sistema de Controle de Bastão - Informática TJMG

Sistema completo de gerenciamento de fila e atendimento para equipes de suporte técnico, desenvolvido em Streamlit com autenticação, persistência de dados e sincronização em tempo real.

---

## 📋 Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Arquitetura](#arquitetura)
- [Estrutura de Arquivos](#estrutura-de-arquivos)
- [Segurança](#segurança)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Sobre o Projeto

O **Sistema de Controle de Bastão** é uma aplicação web desenvolvida para gerenciar o fluxo de atendimento em equipes de suporte técnico. O sistema implementa uma fila rotativa onde colaboradores assumem o "bastão" (responsabilidade pelo próximo atendimento) de forma automática e justa.

### Caso de Uso

Imagine uma equipe de 16 técnicos de informática que precisa:
- ✅ Distribuir atendimentos de forma justa
- ✅ Saber quem é o próximo responsável
- ✅ Controlar pausas (almoço, saídas rápidas)
- ✅ Registrar atividades e demandas
- ✅ Gerar relatórios de produtividade

**Este sistema resolve tudo isso!**

---

## ✨ Funcionalidades

### 🔐 Autenticação e Usuários
- Login seguro com usuário e senha
- Dois níveis de acesso: **Administrador** e **Colaborador**
- Troca obrigatória de senha no primeiro acesso
- Sessão persistente (F5 mantém login)
- Sincronização entre múltiplos dispositivos

### 📊 Gerenciamento de Fila
- **Fila rotativa automática:** Próximo colaborador assume o bastão ao finalizar atendimento
- **Entrada/saída dinâmica:** Colaboradores podem entrar e sair da fila via checkbox
- **Bastão automático:** Se ninguém tem o bastão, primeiro da fila assume automaticamente
- **Visualização em tempo real:** Mostra responsável atual, próximo na fila e aguardando

### ⏰ Controle de Status
- **Na Fila:** Disponível para atendimento
- **Almoço:** Pausa de 1 hora (sai automaticamente após 60 min)
- **Saída Rápida:** Pausa curta
- **Ausente:** Indisponível
- **Em Demanda:** Trabalhando em atividade específica
- **Indisponível:** Fora da fila

### 📋 Gerenciamento de Demandas
- Criação de demandas públicas (visíveis para todos)
- Categorização por setor (Geral, Rede, Infraestrutura, etc.)
- Direcionamento específico para colaboradores
- Priorização (Alta, Média, Baixa)
- Registro de tempo de início e duração
- Histórico completo de demandas finalizadas

### 📈 Relatórios e Métricas
- **Tempo com bastão:** Duração atual do responsável
- **Rodadas hoje:** Quantas vezes cada um pegou o bastão
- **Ranking diário:** Classificação por número de atendimentos
- **Logs de demandas:** Histórico completo com timestamps
- **Relatórios administrativos:** Análises detalhadas (admin only)

### 🎨 Interface Moderna
- Design profissional com gradientes e sombras
- Light mode otimizado para trabalho prolongado
- Responsivo e adaptável
- Card de usuário no canto superior direito
- Título centralizado com identidade visual
- Status coloridos e intuitivos

### ⚡ Funcionalidades Avançadas
- **Auto-refresh (3s):** Sincronização automática entre dispositivos
- **Estado compartilhado:** Arquivo JSON como banco de dados
- **Thread-safe:** Lock para evitar corrupção de dados
- **Persistência completa:** Nada se perde ao recarregar
- **Painel administrativo:** Gestão de usuários e demandas

---

## 🛠️ Tecnologias

### Core
- **Python 3.10+**
- **Streamlit 1.31.0+** - Framework web
- **SQLite3** - Banco de dados de usuários
- **JSON** - Armazenamento de estado compartilhado

### Bibliotecas
```txt
streamlit>=1.31.0
streamlit-autorefresh>=1.0.1
pandas>=2.0.0
pytz>=2023.3
```

---

## 📥 Instalação

### Pré-requisitos
- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)

### Passo a Passo

1. **Clone o repositório:**
```bash
git clone https://github.com/seu-usuario/controle-bastao.git
cd controle-bastao
```

2. **Crie um ambiente virtual (recomendado):**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

4. **Execute a aplicação:**
```bash
streamlit run app_informatica_com_cache.py
```

5. **Acesse no navegador:**
```
http://localhost:8501
```

### Personalização

**Editar colaboradores:**
```python
# Em app_informatica_com_cache.py (linha ~52)
COLABORADORES = [
    "Seu Nome 1",
    "Seu Nome 2",
    # ...
]
```

**Ajustar auto-refresh:**
```python
# Em app_informatica_com_cache.py (linha ~1192)
st_autorefresh(interval=3000)  # 3000ms = 3 segundos
```

---

## 📖 Uso

### Para Colaboradores

#### Login
1. Acesse a aplicação
2. Selecione seu nome
3. Digite sua senha (padrão: user123)
4. Clique em "Entrar"
5. Troque a senha no primeiro acesso

#### Gerenciar Status
- **Almoço:** Clique em "Almoço" (sai da fila por 1 hora)
- **Saída:** Clique em "Saída" (pausa rápida)
- **Ausente:** Clique em "Ausente" (indisponível)
- **Voltar:** Marque o checkbox ao lado do seu nome

#### Registrar Atividades
1. Clique em "Atividades"
2. Digite ou selecione a demanda
3. Clique em "Iniciar"
4. Quando terminar: clique em "✅"

### Para Administradores

#### Acessar Painel Admin
1. Faça login como admin
2. Clique em "Admin" nas ferramentas
3. Acesse as abas:
   - Cadastrar Colaborador
   - Gerenciar Demandas
   - Banco de Dados

#### Criar Demanda Pública
1. Aba "Gerenciar Demandas"
2. Preencha descrição, prioridade e setor
3. Direcione para colaborador (opcional)
4. Clique em "Criar Demanda"

---

## 🏗️ Arquitetura

### Componentes Principais

1. **app_informatica_com_cache.py** - Interface e lógica principal
2. **shared_state.py** - Gerenciamento de estado compartilhado
3. **login_screen.py** - Sistema de autenticação
4. **auth_system.py** - Banco de dados SQLite
5. **admin_bd_panel.py** - Painel administrativo

### Sincronização em Tempo Real

```
PC1 (Marcio) → Mudança de status
     ↓
SharedState.sync_from_session_state()
     ↓
bastao_state.json (atualizado)
     ↓
Auto-refresh (3s em todos os PCs)
     ↓
SharedState.sync_to_session_state()
     ↓
PC2 e PC3 veem a mudança ✅
```

---

## 📁 Estrutura de Arquivos

```
controle-bastao/
├── app_informatica_com_cache.py    # Aplicação principal
├── shared_state.py                  # Estado compartilhado
├── login_screen.py                  # Sistema de login
├── auth_system.py                   # Autenticação
├── admin_bd_panel.py                # Painel admin
├── requirements.txt                 # Dependências
├── README.md                        # Documentação
│
├── bastao_users.db                  # Banco de dados (auto)
├── bastao_state.json                # Estado compartilhado (auto)
└── admin_data.json                  # Dados admin (auto)
```

---

## 🔒 Segurança

### Implementações de Segurança
- ✅ Senhas hasheadas (SHA256)
- ✅ Sessões isoladas por navegador
- ✅ Query param para persistência (?user=Nome)
- ✅ Thread-safe com locks
- ✅ Controle de acesso por nível (Admin/Colaborador)

### Boas Práticas
- Nunca armazene senhas em plain text
- Troque a senha padrão no primeiro acesso
- Faça backup regular de `bastao_users.db`

---

## 🐛 Troubleshooting

### F5 desloga

**Solução:** Verifique se `st.query_params['user']` está sendo salvo no login.

### Usuários não se veem

**Solução:** 
1. Verifique se `bastao_state.json` existe
2. Confirme que `SharedState.sync_from_session_state()` é chamado após mudanças

### Bastão não passa automaticamente

**Solução:** Certifique-se que `check_and_assume_baton()` está sendo chamado em:
- `toggle_queue()`
- `rotate_bastao()`
- `finalizar_demanda()`
- Ao entrar na fila após login

### Banco de dados corrompido

**Solução:**
```bash
cp bastao_users.db bastao_users.db.backup
rm bastao_users.db
# Reinicie - banco será recriado
```

---

## 🚀 Deploy

### Streamlit Cloud

1. **Push para GitHub:**
```bash
git init
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Deploy:**
- Acesse: https://share.streamlit.io
- Conecte GitHub
- Selecione repositório
- Defina: `app_informatica_com_cache.py`
- Deploy

---

## 📊 Métricas Rastreadas

- **Rodadas por Colaborador:** Quantas vezes pegou o bastão
- **Tempo Médio com Bastão:** Duração média
- **Taxa de Disponibilidade:** % do tempo na fila
- **Demandas Finalizadas:** Total e por colaborador
- **Tempo de Resposta:** Tempo até pegar o bastão

---

## 🎯 Roadmap

### Versão Atual: 1.0.0
- ✅ Sistema de fila completo
- ✅ Autenticação e autorização
- ✅ Sincronização em tempo real
- ✅ Gerenciamento de demandas
- ✅ Relatórios básicos

### Próximas Versões
- [ ] Dark mode opcional
- [ ] Notificações push
- [ ] Exportação de relatórios (PDF/Excel)
- [ ] Integração com Slack/Teams
- [ ] API REST
- [ ] Dashboard analytics

---

## 📝 Licença

Este projeto está sob a licença MIT.

---

## 👥 Equipe

**Desenvolvido para:** Setor de Informática - TJMG

**Colaboradores:** 16 técnicos de informática

---

<div align="center">

**Desenvolvido para a equipe de Informática TJMG**

*Sistema de Controle de Bastão v1.0.0*

</div>
