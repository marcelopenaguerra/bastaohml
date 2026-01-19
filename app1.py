# ============================================
# CONTROLE DE BASTÃO Informática 2026
# Versão: Completa com Login e Banco de Dados
# ============================================
import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta, date, time as dt_time
import pytz  # Timezone de Brasília
from operator import itemgetter
from streamlit_autorefresh import st_autorefresh
import random
import base64
import os

import json
from pathlib import Path

# Sistema de autenticação
from auth_system import init_database, verificar_login, listar_usuarios_ativos, adicionar_usuario, is_usuario_admin
from login_screen import verificar_autenticacao, mostrar_tela_login, fazer_logout
from admin_bd_panel import mostrar_painel_admin_bd, adicionar_menu_bd_sidebar

# Sistema de Estado Compartilhado
from shared_state import SharedState

# Timezone de Brasília
BRASILIA_TZ = pytz.timezone('America/Sao_Paulo')

def now_brasilia():
    """Retorna datetime atual no horário de Brasília"""
    return datetime.now(BRASILIA_TZ)

# ==================== FORÇAR LIGHT MODE ====================
st.set_page_config(
    page_title="Controle de Bastão - Informática",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Sistema de Controle de Bastão - Informática TJMG"
    }
)

# Forçar tema claro via CSS
st.markdown("""
<style>
    /* Forçar tema claro */
    :root {
        color-scheme: light !important;
    }
    
    [data-testid="stAppViewContainer"] {
        background-color: #f1f5f9 !important;
    }
    
    /* Remover opção de dark mode do menu */
    button[kind="header"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Arquivo de persistência
STATE_FILE = Path("bastao_state.json")
ADMIN_FILE = Path("admin_data.json")

# --- ADMINISTRADORES ---
# Colaboradores com permissão para cadastrar colaboradores e demandas
ADMIN_COLABORADORES = [
    "Daniely Cristina Cunha Mesquita",
    "Marcio Rodrigues Alves",
    "Leonardo goncalves fleury"
]

# --- Inicializar banco PRIMEIRO ---
# Criar banco se não existir (ANTES de tentar listar usuários)
init_database()

# --- Função para obter colaboradores do banco ---
def get_colaboradores():
    """Retorna lista atualizada de colaboradores do banco de dados"""
    try:
        return listar_usuarios_ativos()
    except:
        # Se falhar, retornar lista vazia (banco ainda não existe)
        return []

# PROBLEMA 6: Lista dinâmica (atualiza quando novo usuário é criado)
COLABORADORES = get_colaboradores()

# --- Constantes de Opções ---
REG_USUARIO_OPCOES = ["Cartório", "Externo"]
REG_SISTEMA_OPCOES = ["Conveniados", "Outros", "Eproc", "Themis", "JPE", "SIAP"]
REG_CANAL_OPCOES = ["Presencial", "Telefone", "Email", "Whatsapp", "Outros"]
REG_DESFECHO_OPCOES = ["Resolvido - Informática", "Escalonado"]


# Emoji do Bastão (removido - sem emoji)
BASTAO_EMOJI = ""

# ============================================
# FUNÇÕES AUXILIARES
# ============================================


def save_state():
    """Salva estado atual - USA SHARED STATE"""
    SharedState.sync_from_session_state()

def load_state():
    """Carrega estado - USA SHARED STATE"""
    SharedState.sync_to_session_state()
    return True

def save_admin_data():
    """Salva dados administrativos"""
    SharedState.save_admin_data()

def load_admin_data():
    """Carrega dados administrativos"""
    return SharedState.load_admin_data()

def check_admin_auth():
    """Verifica se o usuário logado é admin"""
    return st.session_state.get('is_admin', False)

def apply_modern_styles():
    """Aplica design profissional moderno - FORÇAR LIGHT MODE"""
    st.markdown("""<style>
    /* Importar fonte moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* ==================== FORÇAR LIGHT MODE ==================== */
    /* FORÇA cores em TODOS os elementos */
    
    html, body, [data-testid="stAppViewContainer"], 
    .main, .block-container, [class*="st-"] {
        background: #f1f5f9 !important;
        color: #0f172a !important;
    }
    
    /* FORÇAR textos pretos em TUDO */
    p, span, div, label, h1, h2, h3, h4, h5, h6, 
    .stMarkdown, .stText, .stCaption {
        color: #0f172a !important;
    }
    
    /* Labels específicos */
    label {
        color: #1e293b !important;
        font-weight: 500 !important;
    }
    
    /* Reset e Base */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Container principal */
    .main {
        background: #f1f5f9 !important;
        padding: 1.5rem !important;
    }
    
    .block-container {
        max-width: 1400px !important;
        padding: 1rem !important;
        background: #f1f5f9 !important;
    }
    
    /* Remover header padrão Streamlit */
    header {
        background: transparent !important;
    }
    
    /* Botões modernos */
    .stButton > button {
        background: white !important;
        color: #0f172a !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        transition: all 0.15s ease !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }
    
    .stButton > button:hover {
        background: #f8fafc !important;
        border-color: #cbd5e1 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08) !important;
        transform: translateY(-1px) !important;
    }
    
    .stButton > button[kind="primary"] {
        background: #2563eb !important;
        color: white !important;
        border-color: #2563eb !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: #1d4ed8 !important;
        border-color: #1d4ed8 !important;
    }
    
    /* Inputs - FORÇAR PRETO */
    .stSelectbox > div > div,
    .stTextInput > div > div,
    .stTextArea > div > div,
    input, select, textarea {
        border-radius: 10px !important;
        border: 1px solid #e2e8f0 !important;
        background: white !important;
        color: #0f172a !important;
        font-size: 0.875rem !important;
    }
    
    /* Placeholder visível */
    input::placeholder, 
    textarea::placeholder {
        color: #94a3b8 !important;
        opacity: 1 !important;
    }
    
    .stSelectbox > div > div:hover {
        border-color: #cbd5e1 !important;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
    }
    
    /* Headers - PRETO FORTE */
    h1, h2, h3, h4, h5, h6 {
        color: #0f172a !important;
        font-weight: 600 !important;
    }
    
    h1 {
        font-size: 1.75rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    h2 {
        font-size: 1.25rem !important;
        margin-bottom: 0.75rem !important;
    }
    
    h3 {
        font-size: 1.1rem !important;
        margin-bottom: 0.5rem !important;
        color: #475569 !important;
    }
    
    /* Alertas */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 10px !important;
        border: 1px solid !important;
        padding: 0.875rem !important;
        font-size: 0.875rem !important;
    }
    
    .stSuccess {
        background: #f0fdf4 !important;
        border-color: #bbf7d0 !important;
        color: #166534 !important;
    }
    
    .stError {
        background: #fef2f2 !important;
        border-color: #fecaca !important;
        color: #991b1b !important;
    }
    
    .stWarning {
        background: #fefce8 !important;
        border-color: #fef08a !important;
        color: #854d0e !important;
    }
    
    .stInfo {
        background: #eff6ff !important;
        border-color: #bfdbfe !important;
        color: #1e40af !important;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: white !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        padding: 0.875rem !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: #f8fafc !important;
        border-color: #cbd5e1 !important;
    }
    
    /* Sidebar - FORÇAR LIGHT */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] * {
        background: white !important;
        color: #0f172a !important;
    }
    
    [data-testid="stSidebar"] {
        border-right: 1px solid #e2e8f0 !important;
    }
    
    /* Sidebar headers */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {
        color: #0f172a !important;
    }
    
    /* Métricas - PRETO FORTE */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        color: #0f172a !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.875rem !important;
        color: #475569 !important;
        font-weight: 500 !important;
    }
    
    /* ==================== CHECKBOX PADRÃO (igual aos da fila) ==================== */
    /* Sem customização - usar aparência nativa */
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }
    
    /* Divisor */
    hr {
        border: none !important;
        height: 1px !important;
        background: #e2e8f0 !important;
        margin: 1.5rem 0 !important;
    }
    
    /* Tabelas */
    .dataframe {
        font-size: 0.875rem !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }
    
    .dataframe thead th {
        background: #f8fafc !important;
        color: #0f172a !important;
        font-weight: 600 !important;
        padding: 0.75rem !important;
        border-bottom: 2px solid #e2e8f0 !important;
    }
    
    .dataframe tbody td {
        padding: 0.75rem !important;
        border-bottom: 1px solid #f1f5f9 !important;
        color: #0f172a !important;
    }
    
    /* Animação de demandas piscando */
    @keyframes pulse-demand {
        0%, 100% { 
            opacity: 1;
            transform: scale(1);
        }
        50% { 
            opacity: 0.7;
            transform: scale(1.02);
        }
    }
    
    .demand-alert {
        animation: pulse-demand 2s infinite;
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid #f59e0b;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(245, 158, 11, 0.2);
    }
    
    .demand-alert strong {
        color: #92400e !important;
        font-size: 1rem;
    }
    
    /* Checkbox - FORÇAR VISÍVEL */
    .stCheckbox {
        font-size: 0.875rem !important;
    }
    
    .stCheckbox label,
    .stCheckbox span {
        color: #0f172a !important;
    }
    
    /* Caption - FORÇAR CINZA ESCURO */
    .stCaption,
    [data-testid="stCaptionContainer"] {
        color: #475569 !important;
        font-style: normal !important;
    }
    
    /* FORÇAR em elementos do Streamlit */
    [class*="st-"] {
        color: #0f172a !important;
    }
    
    /* Texto em colunas */
    [data-testid="column"] p,
    [data-testid="column"] span,
    [data-testid="column"] div {
        color: #0f172a !important;
    }
    
    /* Remover elementos desnecessários */
    .stDeployButton {
        display: none !important;
    }
    
    button[title="View fullscreen"] {
        display: none !important;
    }
    
    /* Responsivo */
    @media (max-width: 768px) {
        .block-container {
            padding: 0.5rem !important;
        }
    }
    </style>""", unsafe_allow_html=True)

def format_time_duration(duration):
    if not isinstance(duration, timedelta): return '--:--:--'
    s = int(duration.total_seconds())
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f'{h:02}:{m:02}:{s:02}'

def init_session_state():
    """Inicializa o estado da sessão"""
    # Se já foi inicializado, não fazer nada
    if 'initialized' in st.session_state:
        return
    
    # Marcar como inicializado
    st.session_state.initialized = True
    
    # Lista de todos os campos necessários com valores padrão
    defaults = {
        'bastao_queue': [],
        'status_texto': {nome: 'Indisponível' for nome in COLABORADORES},
        'bastao_start_time': None,
        'bastao_counts': {nome: 0 for nome in COLABORADORES},
        'active_view': None,
        'simon_sequence': [],
        'simon_user_input': [],
        'simon_status': 'start',
        'simon_level': 1,
        'simon_ranking': [],
        'daily_logs': [],
        'success_message': None,
        'success_message_time': None,
        # Admin fields
        'is_admin': False,
        'colaboradores_extras': [],
        'demandas_publicas': [],
        'almoco_times': {},
        'demanda_logs': [],
        'demanda_start_times': {}
    }
    
    # Tentar carregar estado salvo
    loaded = load_state()
    load_admin_data()  # Carregar dados administrativos
    
    # Inicializar TODOS os campos (mesmo que tenha carregado do JSON)
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default
    
    # Inicializar checkboxes
    for nome in COLABORADORES:
        if f'check_{nome}' not in st.session_state:
            st.session_state[f'check_{nome}'] = False

def find_next_holder_index(current_index, queue):
    if not queue: return -1
    num_colab = len(queue)
    if num_colab == 0: return -1
    next_idx = (current_index + 1) % num_colab
    attempts = 0
    while attempts < num_colab:
        colaborador = queue[next_idx]
        if st.session_state.get(f'check_{colaborador}'): return next_idx
        next_idx = (next_idx + 1) % num_colab
        attempts += 1
    return -1

def check_and_assume_baton():
    queue = st.session_state.bastao_queue
    current_holder = next((c for c, s in st.session_state.status_texto.items() if 'Bastão' in s), None)
    is_current_valid = (current_holder and current_holder in queue and st.session_state.get(f'check_{current_holder}'))
    first_eligible_index = find_next_holder_index(-1, queue)
    first_eligible_holder = queue[first_eligible_index] if first_eligible_index != -1 else None
    
    should_have_baton = None
    if is_current_valid: should_have_baton = current_holder
    elif first_eligible_holder: should_have_baton = first_eligible_holder

    changed = False
    for c in COLABORADORES:
        s_text = st.session_state.status_texto.get(c, '')
        if c != should_have_baton and 'Bastão' in s_text:
            st.session_state.status_texto[c] = 'Indisponível'
            changed = True

    if should_have_baton:
        s_current = st.session_state.status_texto.get(should_have_baton, '')
        if 'Bastão' not in s_current:
            old_status = s_current
            new_status = f"Bastão | {old_status}" if old_status and old_status != "Indisponível" else "Bastão"
            st.session_state.status_texto[should_have_baton] = new_status
            st.session_state.bastao_start_time = now_brasilia()
            changed = True
    elif not should_have_baton:
        if current_holder:
            st.session_state.status_texto[current_holder] = 'Indisponível'
            changed = True
        st.session_state.bastao_start_time = None

    return changed

def toggle_queue(colaborador):
    
    if colaborador in st.session_state.bastao_queue:
        st.session_state.bastao_queue.remove(colaborador)
        st.session_state[f'check_{colaborador}'] = False
        current_s = st.session_state.status_texto.get(colaborador, '')
        if current_s == '' or current_s == 'Bastão':
            st.session_state.status_texto[colaborador] = 'Indisponível'
    else:
        st.session_state.bastao_queue.append(colaborador)
        st.session_state[f'check_{colaborador}'] = True
        current_s = st.session_state.status_texto.get(colaborador, 'Indisponível')
        if current_s == 'Indisponível':
            st.session_state.status_texto[colaborador] = ''

    check_and_assume_baton()
    save_state()  # SALVAR ESTADO APÓS MUDANÇA

def rotate_bastao():
    """Passa o bastão para o próximo colaborador"""
    
    # Verificar quem está selecionado
    selected = st.session_state.get('colaborador_selectbox')
    
    queue = st.session_state.bastao_queue
    current_holder = next((c for c, s in st.session_state.status_texto.items() if 'Bastão' in s), None)
    
    if not current_holder:
        st.warning('⚠️ Ninguém tem o bastão no momento.')
        return
    
    # VALIDAÇÃO: só quem tem o bastão pode passar
    if selected != current_holder:
        st.error(f'❌ Somente **{current_holder}** pode passar o bastão!')
        st.info(f'💡 Selecione "{current_holder}" no menu acima para passar o bastão.')
        return
    
    if not queue or current_holder not in queue:
        st.warning('⚠️ O detentor do bastão não está na fila.')
        check_and_assume_baton()
        return

    try:
        current_index = queue.index(current_holder)
    except ValueError:
        check_and_assume_baton()
        return

    next_idx = find_next_holder_index(current_index, queue)
    
    if next_idx != -1:
        next_holder = queue[next_idx]
        
        old_h_status = st.session_state.status_texto[current_holder]
        new_h_status = old_h_status.replace('Bastão | ', '').replace('Bastão', '').strip()
        if not new_h_status: new_h_status = ''
        st.session_state.status_texto[current_holder] = new_h_status
        
        old_n_status = st.session_state.status_texto.get(next_holder, '')
        new_n_status = f"Bastão | {old_n_status}" if old_n_status else "Bastão"
        st.session_state.status_texto[next_holder] = new_n_status
        st.session_state.bastao_start_time = now_brasilia()
        
        st.session_state.bastao_counts[current_holder] = st.session_state.bastao_counts.get(current_holder, 0) + 1
        
        st.session_state.success_message = f"🎉 Bastão passou de **{current_holder}** para **{next_holder}**!"
        st.session_state.success_message_time = now_brasilia()
        save_state()
        st.rerun()
    else:
        st.warning('⚠️ Não há próximo(a) colaborador(a) elegível na fila.')
        check_and_assume_baton()

def update_status(new_status_part, force_exit_queue=False):
    selected = st.session_state.usuario_logado
    
    if not selected or selected == 'Selecione um nome':
        st.warning('Selecione um(a) colaborador(a).')
        return

    blocking_statuses = ['Almoço', 'Ausente', 'Saída rápida']
    should_exit_queue = new_status_part in blocking_statuses or force_exit_queue
    
    # Registrar horário de almoço
    if new_status_part == 'Almoço':
        st.session_state.almoco_times[selected] = now_brasilia()
    
    # Registrar início de demanda/atividade
    if 'Atividade:' in new_status_part or force_exit_queue:
        if selected not in st.session_state.demanda_start_times:
            st.session_state.demanda_start_times[selected] = now_brasilia()
    
    # CRÍTICO: Se deve sair da fila, remover IMEDIATAMENTE
    if should_exit_queue:
        final_status = new_status_part
        
        # FORÇAR remoção da fila
        st.session_state[f'check_{selected}'] = False
        if selected in st.session_state.bastao_queue:
            st.session_state.bastao_queue.remove(selected)
        
        # Verificar se tinha bastão
        was_holder = 'Bastão' in st.session_state.status_texto.get(selected, '')
        
        # Atualizar status (sem bastão se estava saindo)
        st.session_state.status_texto[selected] = final_status
        
        # Se tinha bastão, passar para próximo
        if was_holder:
            check_and_assume_baton()
    else:
        # Apenas atualizar status sem sair da fila
        current = st.session_state.status_texto.get(selected, '')
        parts = [p.strip() for p in current.split('|') if p.strip()]
        type_of_new = new_status_part.split(':')[0]
        cleaned_parts = []
        for p in parts:
            if p == 'Indisponível': continue
            if p.startswith(type_of_new): continue
            cleaned_parts.append(p)
        cleaned_parts.append(new_status_part)
        cleaned_parts.sort(key=lambda x: 0 if 'Bastão' in x else 1 if 'Atividade' in x else 2)
        final_status = " | ".join(cleaned_parts)
        
        was_holder = next((True for c, s in st.session_state.status_texto.items() if 'Bastão' in s and c == selected), False)
        
        if was_holder and 'Bastão' not in final_status:
            final_status = f"Bastão | {final_status}"
        
        st.session_state.status_texto[selected] = final_status
    
    save_state()  # SALVAR ESTADO APÓS MUDANÇA

def leave_specific_status(colaborador, status_type_to_remove):
    """Remove um status específico e volta para fila se necessário"""
    old_status = st.session_state.status_texto.get(colaborador, '')
    parts = [p.strip() for p in old_status.split('|')]
    new_parts = [p for p in parts if status_type_to_remove not in p and p]
    new_status = " | ".join(new_parts)
    
    # Se ficou sem status, marcar como vazio (não Indisponível, pois vai voltar pra fila)
    if not new_status:
        new_status = ''
    
    st.session_state.status_texto[colaborador] = new_status
    
    # Se estava em Almoço/Saída/Ausente e saiu, VOLTAR PARA FILA
    if status_type_to_remove in ['Almoço', 'Saída rápida', 'Ausente']:
        if colaborador not in st.session_state.bastao_queue:
            st.session_state.bastao_queue.append(colaborador)
            st.session_state[f'check_{colaborador}'] = True
        
        # Limpar tempo de almoço se estava em almoço
        if status_type_to_remove == 'Almoço' and colaborador in st.session_state.get('almoco_times', {}):
            del st.session_state.almoco_times[colaborador]
    
    check_and_assume_baton()
    save_state()  # SALVAR ESTADO

def enter_from_indisponivel(colaborador):
    if colaborador not in st.session_state.bastao_queue:
        st.session_state.bastao_queue.append(colaborador)
    st.session_state[f'check_{colaborador}'] = True
    st.session_state.status_texto[colaborador] = ''
    check_and_assume_baton()
    save_state()  # SALVAR ESTADO

def finalizar_demanda(colaborador):
    """Finaliza demanda e retorna colaborador para fila"""
    # Registrar fim da demanda
    if colaborador in st.session_state.demanda_start_times:
        start_time = st.session_state.demanda_start_times[colaborador]
        end_time = now_brasilia()
        duration = end_time - start_time
        
        # Pegar atividade
        atividade_texto = st.session_state.status_texto.get(colaborador, '')
        
        # Salvar log
        log_entry = {
            'tipo': 'demanda',
            'colaborador': colaborador,
            'atividade': atividade_texto,
            'inicio': start_time.isoformat(),
            'fim': end_time.isoformat(),
            'duracao_minutos': duration.total_seconds() / 60,
            'timestamp': now_brasilia()
        }
        st.session_state.demanda_logs.append(log_entry)
        st.session_state.daily_logs.append(log_entry)
        
        # Limpar tempo de início
        del st.session_state.demanda_start_times[colaborador]
    
    # Limpar status
    st.session_state.status_texto[colaborador] = ''
    
    # Voltar para fila
    if colaborador not in st.session_state.bastao_queue:
        st.session_state.bastao_queue.append(colaborador)
        st.session_state[f'check_{colaborador}'] = True
    
    save_state()
    st.success(f"✅ {colaborador} finalizou a demanda e voltou para a fila!")
    time.sleep(1)
    st.rerun()

def check_almoco_timeout():
    """Verifica se alguém está há mais de 1h no almoço e retorna automaticamente"""
    now = now_brasilia()
    almoco_times = st.session_state.get('almoco_times', {})
    
    for nome in list(almoco_times.keys()):
        saida_time = almoco_times[nome]
        if isinstance(saida_time, str):
            saida_time = datetime.fromisoformat(saida_time)
        
        elapsed_hours = (now - saida_time).total_seconds() / 3600
        
        if elapsed_hours >= 1.0:  # 1 hora
            # Remover do almoço
            if st.session_state.status_texto.get(nome) == 'Almoço':
                st.session_state.status_texto[nome] = ''
            
            # Voltar para fila
            if nome not in st.session_state.bastao_queue:
                st.session_state.bastao_queue.append(nome)
                st.session_state[f'check_{nome}'] = True
            
            # Limpar registro
            del st.session_state.almoco_times[nome]
            save_state()
            
            st.info(f"⏰ {nome} retornou automaticamente do almoço após 1 hora.")
            st.rerun()


def gerar_html_relatorio(logs_filtrados):
    """Gera relatório HTML formatado"""
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Relatório Informática</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .header {
                background: linear-gradient(135deg, #1f4788 0%, #2c5aa0 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                text-align: center;
                margin-bottom: 30px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .header h1 {
                margin: 0 0 10px 0;
                font-size: 28px;
            }
            .header p {
                margin: 5px 0;
                opacity: 0.9;
            }
            .registro {
                background: white;
                padding: 25px;
                margin-bottom: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border-left: 5px solid #2c5aa0;
            }
            .registro-header {
                background-color: #e8f4f8;
                padding: 15px;
                margin: -25px -25px 20px -25px;
                border-radius: 8px 8px 0 0;
                border-bottom: 2px solid #2c5aa0;
            }
            .registro-header h2 {
                margin: 0;
                color: #1f4788;
                font-size: 20px;
            }
            .registro-tipo {
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
                margin-left: 10px;
            }
            .tipo-atendimento {
                background-color: #4CAF50;
                color: white;
            }
            .tipo-horas {
                background-color: #FF9800;
                color: white;
            }
            .tipo-erro {
                background-color: #f44336;
                color: white;
            }
            .campo {
                margin: 12px 0;
                display: flex;
                border-bottom: 1px solid #eee;
                padding-bottom: 8px;
            }
            .campo-label {
                font-weight: bold;
                color: #1f4788;
                min-width: 150px;
                margin-right: 15px;
            }
            .campo-valor {
                color: #333;
                flex: 1;
            }
            .footer {
                text-align: center;
                margin-top: 40px;
                padding: 20px;
                color: #666;
                border-top: 2px solid #ddd;
            }
            @media print {
                body {
                    background-color: white;
                }
                .registro {
                    page-break-inside: avoid;
                    box-shadow: none;
                    border: 1px solid #ddd;
                }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>RELATÓRIO DE REGISTROS - Informática</h1>
            <p>Sistema de Controle de Bastão</p>
            <p><strong>Gerado em:</strong> """ + now_brasilia().strftime("%d/%m/%Y às %H:%M:%S") + """</p>
            <p><strong>Total de registros:</strong> """ + str(len(logs_filtrados)) + """</p>
        </div>
    """
    
    for idx, log in enumerate(logs_filtrados, 1):
        timestamp = log.get('timestamp', now_brasilia())
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except:
                timestamp = now_brasilia()
        
        data_hora = timestamp.strftime("%d/%m/%Y %H:%M:%S")
        colaborador = log.get('colaborador', 'N/A')
        
        # Determina tipo
        if 'usuario' in log:
            tipo = "ATENDIMENTO"
            classe_tipo = "tipo-atendimento"
            icone = "📝"
        elif 'inicio' in log and 'tempo' in log:
            tipo = "HORAS EXTRAS"
            classe_tipo = "tipo-horas"
            icone = "⏰"
        elif 'titulo' in log and 'relato' in log:
            tipo = "ERRO/NOVIDADE"
            classe_tipo = "tipo-erro"
            icone = "Bug:"
        else:
            tipo = "REGISTRO"
            classe_tipo = "tipo-atendimento"
            icone = "📄"
        
        html += f"""
        <div class="registro">
            <div class="registro-header">
                <h2>{icone} REGISTRO #{idx} <span class="registro-tipo {classe_tipo}">{tipo}</span></h2>
            </div>
            
            <div class="campo">
                <div class="campo-label">📅 Data/Hora:</div>
                <div class="campo-valor">{data_hora}</div>
            </div>
            <div class="campo">
                <div class="campo-label">Colaborador:</div>
                <div class="campo-valor">{colaborador}</div>
            </div>
        """
        
        # Campos específicos por tipo
        if 'usuario' in log:
            html += f"""
            <div class="campo">
                <div class="campo-label">Usuário:</div>
                <div class="campo-valor">{log.get('usuario', 'N/A')}</div>
            </div>
            <div class="campo">
                <div class="campo-label">🏢 Setor:</div>
                <div class="campo-valor">{log.get('setor', 'N/A')}</div>
            </div>
            <div class="campo">
                <div class="campo-label">💻 Sistema:</div>
                <div class="campo-valor">{log.get('sistema', 'N/A')}</div>
            </div>
            <div class="campo">
                <div class="campo-label">📝 Descrição:</div>
                <div class="campo-valor">{log.get('descricao', 'N/A')}</div>
            </div>
            <div class="campo">
                <div class="campo-label">📞 Canal:</div>
                <div class="campo-valor">{log.get('canal', 'N/A')}</div>
            </div>
            <div class="campo">
                <div class="campo-label">✅ Desfecho:</div>
                <div class="campo-valor">{log.get('desfecho', 'N/A')}</div>
            </div>
            """
        
        elif 'inicio' in log and 'tempo' in log:
            html += f"""
            <div class="campo">
                <div class="campo-label">📅 Data:</div>
                <div class="campo-valor">{log.get('data', 'N/A')}</div>
            </div>
            <div class="campo">
                <div class="campo-label">🕐 Início:</div>
                <div class="campo-valor">{log.get('inicio', 'N/A')}</div>
            </div>
            <div class="campo">
                <div class="campo-label">⏱️ Tempo Total:</div>
                <div class="campo-valor">{log.get('tempo', 'N/A')}</div>
            </div>
            <div class="campo">
                <div class="campo-label">📝 Motivo:</div>
                <div class="campo-valor">{log.get('motivo', 'N/A')}</div>
            </div>
            """
        
        elif 'titulo' in log:
            html += f"""
            <div class="campo">
                <div class="campo-label">📌 Título:</div>
                <div class="campo-valor">{log.get('titulo', 'N/A')}</div>
            </div>
            <div class="campo">
                <div class="campo-label">🎯 Objetivo:</div>
                <div class="campo-valor">{log.get('objetivo', 'N/A')}</div>
            </div>
            <div class="campo">
                <div class="campo-label">🧪 Relato:</div>
                <div class="campo-valor">{log.get('relato', 'N/A')}</div>
            </div>
            <div class="campo">
                <div class="campo-label">🏁 Resultado:</div>
                <div class="campo-valor">{log.get('resultado', 'N/A')}</div>
            </div>
            """
        
        html += "</div>"
    
    html += """
        <div class="footer">
            <p>Sistema de Controle de Bastão - Informática/TJMG</p>
            <p>Relatório gerado automaticamente</p>
        </div>
    </body>
    </html>
    """
    
    return html

def handle_simon_game():
    COLORS = ["🔴", "🔵", "🟢", "🟡"]
    st.markdown("### 🧠 Jogo da Memória (Simon)")
    st.caption("Repita a sequência de cores!")
    
    if st.session_state.simon_status == 'start':
        if st.button("▶️ Iniciar Jogo", use_container_width=True):
            st.session_state.simon_sequence = [random.choice(COLORS)]
            st.session_state.simon_user_input = []
            st.session_state.simon_level = 1
            st.session_state.simon_status = 'showing'
            st.rerun()
            
    elif st.session_state.simon_status == 'showing':
        st.info(f"Nível {st.session_state.simon_level}: Memorize a sequência!")
        cols = st.columns(len(st.session_state.simon_sequence))
        for i, color in enumerate(st.session_state.simon_sequence):
            with cols[i]:
                st.markdown(f"<h1 style='text-align: center;'>{color}</h1>", unsafe_allow_html=True)
        st.markdown("---")
        if st.button("🙈 Já decorei! Responder", type="primary", use_container_width=True):
            st.session_state.simon_status = 'playing'
            st.rerun()
            
    elif st.session_state.simon_status == 'playing':
        st.markdown(f"**Nível {st.session_state.simon_level}** - Clique na ordem:")
        c1, c2, c3, c4 = st.columns(4)
        pressed = None
        if c1.button("🔴", use_container_width=True): pressed = "🔴"
        if c2.button("🔵", use_container_width=True): pressed = "🔵"
        if c3.button("🟢", use_container_width=True): pressed = "🟢"
        if c4.button("🟡", use_container_width=True): pressed = "🟡"
        
        if pressed:
            st.session_state.simon_user_input.append(pressed)
            current_idx = len(st.session_state.simon_user_input) - 1
            if st.session_state.simon_user_input[current_idx] != st.session_state.simon_sequence[current_idx]:
                st.session_state.simon_status = 'lost'
                st.rerun()
            elif len(st.session_state.simon_user_input) == len(st.session_state.simon_sequence):
                st.success("Correto! Próximo nível...")
                time.sleep(0.5)
                st.session_state.simon_sequence.append(random.choice(COLORS))
                st.session_state.simon_user_input = []
                st.session_state.simon_level += 1
                st.session_state.simon_status = 'showing'
                st.rerun()
                
        if st.session_state.simon_user_input:
            st.markdown(f"Sua resposta: {' '.join(st.session_state.simon_user_input)}")
            
    elif st.session_state.simon_status == 'lost':
        st.error(f"❌ Errou! Você chegou ao Nível {st.session_state.simon_level}.")
        st.markdown(f"Sequência correta era: {' '.join(st.session_state.simon_sequence)}")
        
        colaborador = st.session_state.usuario_logado
        if colaborador and colaborador != 'Selecione um nome':
            score = st.session_state.simon_level
            current_ranking = st.session_state.simon_ranking
            found = False
            for entry in current_ranking:
                if entry['nome'] == colaborador:
                    if score > entry['score']:
                        entry['score'] = score
                    found = True
                    break
            if not found:
                current_ranking.append({'nome': colaborador, 'score': score})
            st.session_state.simon_ranking = sorted(current_ranking, key=lambda x: x['score'], reverse=True)[:5]
            st.success(f"Pontuação salva para {colaborador}!")
        else:
            st.warning("Selecione seu nome no menu superior para salvar no Ranking.")
            
        if st.button("Tentar Novamente"):
            st.session_state.simon_status = 'start'
            st.rerun()
            
    st.markdown("---")
    st.subheader("🏆 Ranking Global (Top 5)")
    ranking = st.session_state.simon_ranking
    if not ranking:
        st.markdown("_Nenhum recorde ainda._")
    else:
        df_rank = pd.DataFrame(ranking)
        st.table(df_rank)

def toggle_view(view_name):
    if st.session_state.active_view == view_name:
        st.session_state.active_view = None
    else:
        st.session_state.active_view = view_name

# ============================================
# INTERFACE PRINCIPAL
# ============================================

st.set_page_config(page_title="Controle Bastão Informática 2026", layout="wide", page_icon="🎯")
# ==================== INICIALIZAÇÃO ====================
# Banco já foi inicializado no topo (antes de carregar COLABORADORES)

# Inicializar sessão
init_session_state()
apply_modern_styles()

# ==================== VERIFICAÇÃO DE LOGIN ====================
verificar_autenticacao()  # Se não logado, mostra tela de login e para

# ==================== SINCRONIZAÇÃO DE ESTADO ====================
# Carregar estado do disco APENAS na primeira vez que loga
if 'estado_inicial_carregado' not in st.session_state:
    SharedState.sync_to_session_state()
    st.session_state.estado_inicial_carregado = True

# A partir daqui, usuário está autenticado e tem estado sincronizado

# Adicionar automaticamente na fila ao fazer login (se não estiver)
usuario_atual = st.session_state.usuario_logado

# Verificar se está em status bloqueante
status_atual = st.session_state.status_texto.get(usuario_atual, '')
statuses_bloqueantes = ['Almoço', 'Ausente', 'Saída rápida', 'Atividade:']
esta_bloqueado = any(status in status_atual for status in statuses_bloqueantes)

# Só adiciona se NÃO está na fila E NÃO está bloqueado
# IMPORTANTE: A verificação "not in bastao_queue" JÁ impede duplicatas
if usuario_atual not in st.session_state.bastao_queue and not esta_bloqueado:
    st.session_state.bastao_queue.append(usuario_atual)
    st.session_state[f'check_{usuario_atual}'] = True
    if st.session_state.status_texto.get(usuario_atual) == 'Indisponível':
        st.session_state.status_texto[usuario_atual] = ''
    
    check_and_assume_baton()
    save_state()

st.components.v1.html("<script>window.scrollTo(0, 0);</script>", height=0)

# ==================== ENTRADA RÁPIDA ====================
st.markdown("---")


# Auto-refresh
# Auto-refresh a cada 3 segundos para sincronização em tempo real
st_autorefresh(interval=3000, key='auto_rerun_key')

# Verificar timeout de almoço (1 hora)
check_almoco_timeout()

# ==================== HEADER ====================
# Título centralizado no topo
st.markdown("""
<style>
.header-card {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    border-bottom: 3px solid #2563eb;
}

.header-title {
    color: #0f172a;
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
    text-align: center;
}

.header-subtitle {
    color: #64748b;
    margin: 0.5rem 0 0 0;
    font-size: 0.95rem;
    font-weight: 500;
    text-align: center;
}
</style>

<div class="header-card">
    <h1 class="header-title">Controle de Bastão</h1>
    <p class="header-subtitle">Setor de Informática • TJMG • 2026</p>
</div>
""", unsafe_allow_html=True)

# ==================== CARD DE USUÁRIO ====================
# Card de usuário no canto superior direito
col_spacer, col_user_header = st.columns([3, 1])

with col_user_header:
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 0.75rem 1rem; 
                border-radius: 8px; 
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                text-align: right;
                margin-top: 0.5rem;'>
        <div style='color: white; font-size: 0.95rem; font-weight: 600; margin-bottom: 0.15rem;'>
            {st.session_state.usuario_logado}
        </div>
        <div style='color: rgba(255,255,255,0.8); font-size: 0.75rem;'>
            {'Admin' if st.session_state.is_admin else 'Colaborador'}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botão Sair
    if st.button("Sair", help="Fazer Logout", use_container_width=True, key="btn_logout_header"):
        usuario_atual = st.session_state.usuario_logado
        if usuario_atual:
            if usuario_atual in st.session_state.bastao_queue:
                st.session_state.bastao_queue.remove(usuario_atual)
            st.session_state.status_texto[usuario_atual] = 'Ausente'
            st.session_state[f'check_{usuario_atual}'] = False
            SharedState.sync_from_session_state()
        fazer_logout()

st.markdown("---")

# Layout principal - mesma proporção do header (3:1)
col_principal, col_disponibilidade = st.columns([3, 1])
queue = st.session_state.bastao_queue
responsavel = next((c for c, s in st.session_state.status_texto.items() if 'Bastão' in s), None)

current_index = queue.index(responsavel) if responsavel in queue else -1
proximo_index = find_next_holder_index(current_index, queue)
proximo = queue[proximo_index] if proximo_index != -1 else None

restante = []
if proximo_index != -1:
    num_q = len(queue)
    start_check_idx = (proximo_index + 1) % num_q
    current_check_idx = start_check_idx
    checked_count = 0
    while checked_count < num_q:
        if current_check_idx == start_check_idx and checked_count > 0:
            break
        if 0 <= current_check_idx < num_q:
            colaborador = queue[current_check_idx]
            if colaborador != responsavel and colaborador != proximo and st.session_state.get(f'check_{colaborador}'):
                restante.append(colaborador)
        current_check_idx = (current_check_idx + 1) % num_q
        checked_count += 1

with col_principal:
    if responsavel:
        # Barra sticky que fica fixa no topo ao rolar
        st.markdown(f"""
        <style>
        .sticky-bar {{
            position: fixed;
            top: 3.5rem;
            left: 0;
            right: 0;
            background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
            color: white;
            padding: 0.75rem 1.5rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            z-index: 999;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            font-size: 1rem;
            font-weight: 600;
            opacity: 0;
            transition: opacity 0.3s ease;
        }}
        
        .sticky-bar.visible {{
            opacity: 1;
        }}
        
        .sticky-label {{
            font-size: 0.75rem;
            font-weight: 500;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .sticky-nome {{
            font-size: 1.1rem;
            font-weight: 700;
        }}
        </style>
        
        <div class="sticky-bar" id="stickyBar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style="flex-shrink: 0;">
                <rect x="10" y="2" width="4" height="20" rx="2" fill="white"/>
                <circle cx="12" cy="3" r="2" fill="white"/>
            </svg>
            <span class="sticky-label">Bastão com:</span>
            <span class="sticky-nome">{responsavel}</span>
        </div>
        
        <script>
        window.addEventListener('scroll', function() {{
            const stickyBar = document.getElementById('stickyBar');
            if (window.scrollY > 300) {{
                stickyBar.classList.add('visible');
            }} else {{
                stickyBar.classList.remove('visible');
            }}
        }});
        </script>
        """, unsafe_allow_html=True)
        
        # Card normal do responsável
        st.markdown(f"""
        <style>
        .responsavel-card {{
            background: white;
            border: 2px solid #e2e8f0;
            padding: 1rem;
            border-radius: 12px;
            margin-bottom: 0.75rem;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }}
        
        .responsavel-label {{
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #64748b;
            margin-bottom: 0.5rem;
        }}
        
        .responsavel-nome {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #1e293b;
            line-height: 1.2;
        }}
        </style>
        
        <div class="responsavel-card">
            <div>
                <div class="responsavel-label">
                    Responsável Atual
                </div>
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div class="responsavel-nome">
                        {responsavel}
                    </div>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" style="flex-shrink: 0; opacity: 0.6;">
                        <rect x="10" y="2" width="4" height="20" rx="2" fill="#2563eb"/>
                        <circle cx="12" cy="3" r="2" fill="#2563eb"/>
                    </svg>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Métricas em cards separados
        col_metric1, col_metric2 = st.columns(2)
        
        duration = timedelta()
        if st.session_state.bastao_start_time:
            duration = now_brasilia() - st.session_state.bastao_start_time
        
        with col_metric1:
            st.markdown(f"""
            <style>
            .metric-card {{
                background: white;
                border: 1px solid #e2e8f0;
                padding: 0.875rem;
                border-radius: 10px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            }}
            
            .metric-label {{
                color: #64748b;
                font-size: 0.8rem;
                font-weight: 500;
                margin-bottom: 0.375rem;
            }}
            
            .metric-value {{
                color: #1e293b;
                font-size: 1.25rem;
                font-weight: 700;
            }}
            </style>
            
            <div class="metric-card">
                <div class="metric-label">
                    ⏱️ Tempo com Bastão
                </div>
                <div class="metric-value">
                    {format_time_duration(duration)}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_metric2:
            rodadas = st.session_state.bastao_counts.get(responsavel, 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">
                    Rodadas Hoje
                </div>
                <div class="metric-value">
                    {rodadas}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # ========== DEMANDAS PÚBLICAS PISCANDO (ITEM 10) ==========
        # CRÍTICO: Filtrar por usuario_logado, NÃO por quem tem o bastão
        usuario_logado = st.session_state.usuario_logado
        demandas_ativas = [
            d for d in st.session_state.get('demandas_publicas', []) 
            if d.get('ativa', True) and (
                d.get('direcionada_para') is None or 
                d.get('direcionada_para') == usuario_logado
            )
        ]
        
        if demandas_ativas:
            st.markdown(f"""
            <div class="demand-alert">
                <strong>{len(demandas_ativas)} DEMANDA(S) DISPONÍVEL(EIS) PARA ADESÃO</strong>
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar até 3 demandas
            for dem in demandas_ativas[:3]:
                # Setor antes do título
                setor = dem.get('setor', 'Geral')
                prioridade = dem.get('prioridade', 'Média')
                
                # Limpeza BRUTAL do texto
                texto_limpo = dem['texto'].strip()
                
                # Remove tudo que parecer lixo no início (arr, _arl, .arr, etc)
                import re
                # Remove qualquer combinação de pontos, underscores, letras seguidas de [
                texto_limpo = re.sub(r'^[._]*[a-z]*\[', '[', texto_limpo)
                
                # Se ainda tem [ no início, remove [Setor] e [Prioridade] duplicados
                if texto_limpo.startswith('['):
                    texto_limpo = texto_limpo.replace(f'[{setor}]', '', 1).strip()
                    texto_limpo = texto_limpo.replace(f'[{prioridade}]', '', 1).strip()
                
                titulo = f"[{setor}] [{prioridade}] {texto_limpo[:50]}..."
                
                with st.expander(titulo):
                    st.write(f"**Setor:** {setor}")
                    st.write(f"**Prioridade:** {prioridade}")
                    st.write(f"**Descrição:** {texto_limpo}")
                    st.caption(f"Criada por: {dem.get('criado_por', 'Admin')}")
                    
                    # Verificar se é direcionada
                    if dem.get('direcionada_para'):
                        st.info(f"📌 Esta demanda foi direcionada especificamente para você!")
                    
                    if st.button(f"Aderir a esta demanda", key=f"aderir_dem_{dem['id']}", use_container_width=True):
                        # CRÍTICO: Pegar colaborador logado, NÃO o responsável atual
                        colaborador_logado = st.session_state.usuario_logado
                        
                        # Entrar na demanda automaticamente
                        atividade_desc = f"[{setor}] {texto_limpo[:100]}"
                        
                        # Registrar início
                        st.session_state.demanda_start_times[colaborador_logado] = now_brasilia()
                        
                        # Atualizar status
                        st.session_state.status_texto[colaborador_logado] = f"Atividade: {atividade_desc}"
                        
                        # Sair da fila
                        if colaborador_logado in st.session_state.bastao_queue:
                            st.session_state.bastao_queue.remove(colaborador_logado)
                        st.session_state[f'check_{colaborador_logado}'] = False
                        
                        # Passar bastão
                        check_and_assume_baton()
                        
                        # CRÍTICO: Marcar demanda como inativa (já foi assumida)
                        dem['ativa'] = False
                        dem['assumida_por'] = colaborador_logado
                        dem['assumida_em'] = now_brasilia().isoformat()
                        save_admin_data()
                        
                        save_state()
                        st.success(f"{responsavel} aderiu à demanda!")
                        time.sleep(1)
                        st.rerun()
    else:
        st.markdown("""
        <style>
        .empty-card {{
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
        }}
        
        .empty-text {{
            color: #1e40af;
            font-weight: 500;
        }}
        
        
            
            .empty-text {{
                color: #60a5fa;
            }}
        }}
        </style>
        
        <div class="empty-card">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">Usuários</div>
            <div class="empty-text">Nenhum colaborador com o bastão</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("")
    st.subheader("Próximos da Fila")
        
    # Exibir mensagem de sucesso se existir
    if st.session_state.get('success_message') and st.session_state.get('success_message_time'):
        elapsed = (now_brasilia() - st.session_state.success_message_time).total_seconds()
        if elapsed < 10:
            st.success(st.session_state.success_message)
        else:
            st.session_state.success_message = None
            st.session_state.success_message_time = None
    
    if proximo:
        st.markdown(f'***1º:*** {proximo}')      
    if restante:
        st.caption(f'**2º em diante:** {", ".join(restante)}')
    if not proximo and not restante:
        if responsavel:
            st.info('ℹ️ Apenas o responsável atual é elegível.')
        else:
            st.info('ℹ️ Ninguém elegível na fila.')
    elif not restante and proximo:
        st.markdown("&nbsp;")
    
    st.markdown("")
    # ========== SIDEBAR - AÇÕES RÁPIDAS ==========
    st.markdown("### Ações Rápidas")
    
    # BOTÃO PASSAR REMOVIDO - Item 8: Ao entrar em atividade, passa automaticamente
    
    # Botão Atividades
    st.button('Atividades', on_click=toggle_view, args=('menu_atividades',), use_container_width=True, help='Marcar como Em Demanda')
    
    st.markdown("")
    
    # Status: Almoço, Saída, Ausente
    row1_c1, row1_c2, row1_c3 = st.columns(3)
    
    row1_c1.button('Almoço', on_click=update_status, args=('Almoço', True,), use_container_width=True)
    row1_c2.button('Saída', on_click=update_status, args=('Saída rápida', True,), use_container_width=True)
    row1_c3.button('Ausente', on_click=update_status, args=('Ausente', True,), use_container_width=True)
    
    st.markdown("")
    
    # Atualizar
    if st.button('Atualizar', use_container_width=True):
        # Recarregar APENAS demandas públicas do disco
        load_admin_data()
        
        # Verificar se tem demandas disponíveis
        usuario_logado = st.session_state.usuario_logado
        demandas_disponiveis = [
            d for d in st.session_state.get('demandas_publicas', [])
            if d.get('ativa', True) and (
                d.get('direcionada_para') is None or
                d.get('direcionada_para') == usuario_logado
            )
        ]
        
        if demandas_disponiveis:
            st.toast(f"✅ {len(demandas_disponiveis)} demanda(s) disponível(is)!", icon="✅")
        else:
            st.toast("ℹ️ Nenhuma demanda cadastrada no momento", icon="ℹ️")
    
    # Menu de Atividades
    if st.session_state.active_view == 'menu_atividades':
        with st.container(border=True):
            st.markdown("### 📋 Atividade / Em Demanda")
            
            atividade_desc = st.text_input("Descrição da atividade:", placeholder="Ex: Suporte técnico, Desenvolvimento...")
            
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                if st.button("Confirmar Atividade", type="primary", use_container_width=True):
                    if atividade_desc:
                        colaborador = st.session_state.usuario_logado
                        
                        # Verificar se tem o bastão
                        tem_bastao = 'Bastão' in st.session_state.status_texto.get(colaborador, '')
                        
                        # Registrar início da demanda
                        st.session_state.demanda_start_times[colaborador] = now_brasilia()
                        
                        # Atualizar status (remove da fila)
                        status_final = f"Atividade: {atividade_desc}"
                        update_status(status_final, force_exit_queue=True)
                        
                        # Se tinha bastão, passa automaticamente
                        if tem_bastao:
                            # Limpar bastão do status
                            st.session_state.status_texto[colaborador] = status_final
                            # Passar para próximo
                            check_and_assume_baton()
                            st.success(f"✅ {colaborador} entrou em atividade e o bastão foi passado automaticamente!")
                        else:
                            st.success(f"✅ {colaborador} entrou em atividade!")
                        
                        st.session_state.active_view = None
                        save_state()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.warning("Digite a descrição da atividade.")
            with col_a2:
                if st.button("Cancelar", use_container_width=True, key='cancel_atividade'):
                    st.session_state.active_view = None
                    st.rerun()
    
    st.markdown("---")
    
    # Ferramentas
    st.markdown("### Ferramentas")
    
    # Admins têm mais um botão
    if st.session_state.is_admin:
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.button("Atendimento", help="Registrar Atendimento", use_container_width=True, on_click=toggle_view, args=("atendimentos",))
        col2.button("Erro/Novidade", help="Relatar Erro ou Novidade", use_container_width=True, on_click=toggle_view, args=("erro_novidade",))
        col3.button("Relatórios", help="Ver Registros Salvos", use_container_width=True, on_click=toggle_view, args=("relatorios",))
        col4.button("Admin", help="Painel Administrativo", use_container_width=True, on_click=toggle_view, args=("admin_panel",), type="primary")
        col5.button("Descanso", help="Jogo e Ranking", use_container_width=True, on_click=toggle_view, args=("descanso",))
    else:
        col1, col2, col3 = st.columns(3)
        col1.button("Atendimento", help="Registrar Atendimento", use_container_width=True, on_click=toggle_view, args=("atendimentos",))
        col2.button("Erro/Novidade", help="Relatar Erro ou Novidade", use_container_width=True, on_click=toggle_view, args=("erro_novidade",))
        col3.button("Descanso", help="Jogo e Ranking", use_container_width=True, on_click=toggle_view, args=("descanso",))
    
    # Views das ferramentas
    if st.session_state.active_view == "atendimentos":
        with st.container(border=True):
            st.markdown("### Registro de Atendimento (Local)")
            at_data = st.date_input("Data:", value=date.today(), format="DD/MM/YYYY", key="at_data")
            at_usuario = st.selectbox("Usuário:", REG_USUARIO_OPCOES, index=None, placeholder="Selecione...", key="at_user")
            at_nome_setor = st.text_input("Nome usuário - Setor:", key="at_setor")
            at_sistema = st.selectbox("Sistema:", REG_SISTEMA_OPCOES, index=None, placeholder="Selecione...", key="at_sys")
            at_descricao = st.text_input("Descrição:", key="at_desc")
            at_canal = st.selectbox("Canal:", REG_CANAL_OPCOES, index=None, placeholder="Selecione...", key="at_channel")
            at_desfecho = st.selectbox("Desfecho:", REG_DESFECHO_OPCOES, index=None, placeholder="Selecione...", key="at_outcome")
            
            if st.button("Salvar Registro Localmente", type="primary", use_container_width=True):
                colaborador = st.session_state.usuario_logado
                if colaborador and colaborador != "Selecione um nome":
                    st.success("✅ Atendimento registrado localmente!")
                    log_entry = {
                        'timestamp': now_brasilia(),
                        'colaborador': colaborador,
                        'data': at_data,
                        'usuario': at_usuario,
                        'setor': at_nome_setor,
                        'sistema': at_sistema,
                        'descricao': at_descricao,
                        'canal': at_canal,
                        'desfecho': at_desfecho
                    }
                    st.session_state.daily_logs.append(log_entry)
                else:
                    st.error("Selecione um colaborador.")
    
    
    elif st.session_state.active_view == "descanso":
        with st.container(border=True):
            handle_simon_game()
    
    elif st.session_state.active_view == "erro_novidade":
        with st.container(border=True):
            st.markdown("### Bug: Registro de Erro ou Novidade (Local)")
            en_titulo = st.text_input("Título:")
            en_objetivo = st.text_area("Objetivo:", height=100)
            en_relato = st.text_area("Relato:", height=200)
            en_resultado = st.text_area("Resultado:", height=150)
            
            if st.button("Salvar Relato Localmente", type="primary", use_container_width=True):
                colaborador = st.session_state.usuario_logado
                if colaborador and colaborador != "Selecione um nome":
                    st.success("✅ Relato salvo localmente!")
                    erro_entry = {
                        'timestamp': now_brasilia(),
                        'colaborador': colaborador,
                        'titulo': en_titulo,
                        'objetivo': en_objetivo,
                        'relato': en_relato,
                        'resultado': en_resultado
                    }
                    st.session_state.daily_logs.append(erro_entry)
                    st.session_state.active_view = None
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error("Selecione um colaborador.")
    
    elif st.session_state.active_view == "relatorios":
        with st.container(border=True):
            st.markdown("### 📊 Relatórios e Registros Salvos")
            
            logs = st.session_state.daily_logs
            
            if not logs:
                st.info("📭 Nenhum registro salvo ainda.")
                st.markdown("---")
                st.markdown("**Como usar:**")
                st.markdown("1. Use as abas acima para registrar atendimentos, horas extras, etc.")
                st.markdown("2. Clique em 'Salvar Localmente'")
                st.markdown("3. Os registros aparecerão aqui!")
            else:
                st.success(f"✅ **{len(logs)} registro(s) encontrado(s)**")
                
                # Filtros
                st.markdown("#### 🔍 Filtros")
                col_f1, col_f2 = st.columns(2)
                
                with col_f1:
                    tipo_filtro = st.selectbox(
                        "Tipo de Registro:",
                        ["Todos", "Atendimentos", "Erros/Novidades", "Demandas Concluídas"]
                    )
                
                with col_f2:
                    colaboradores_nos_logs = list(set([log.get('colaborador', 'N/A') for log in logs]))
                    colaborador_filtro = st.selectbox(
                        "Colaborador:",
                        ["Todos"] + sorted(colaboradores_nos_logs)
                    )
                
                st.markdown("---")
                
                # Filtrar logs
                logs_filtrados = logs.copy()
                
                if tipo_filtro == "Atendimentos":
                    logs_filtrados = [l for l in logs_filtrados if 'usuario' in l]
                elif tipo_filtro == "Erros/Novidades":
                    logs_filtrados = [l for l in logs_filtrados if 'titulo' in l and 'relato' in l]
                elif tipo_filtro == "Demandas Concluídas":
                    logs_filtrados = [l for l in logs_filtrados if l.get('tipo') == 'demanda']
                
                if colaborador_filtro != "Todos":
                    logs_filtrados = [l for l in logs_filtrados if l.get('colaborador') == colaborador_filtro]
                
                st.markdown(f"#### 📋 Exibindo {len(logs_filtrados)} registro(s)")
                
                # Exibir logs
                for idx, log in enumerate(reversed(logs_filtrados), 1):
                    timestamp = log.get('timestamp', now_brasilia())
                    if isinstance(timestamp, str):
                        try:
                            timestamp = datetime.fromisoformat(timestamp)
                        except:
                            timestamp = now_brasilia()
                    
                    data_hora = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                    colaborador = log.get('colaborador', 'N/A')
                    
                    # Identifica tipo de registro
                    if 'usuario' in log:
                        # Atendimento
                        with st.expander(f"📝 #{idx} - Atendimento - {colaborador} - {data_hora}"):
                            st.markdown(f"**Colaborador:** {colaborador}")
                            st.markdown(f"**📅 Data:** {log.get('data', 'N/A')}")
                            st.markdown(f"**Usuário:** {log.get('usuario', 'N/A')}")
                            st.markdown(f"**🏢 Setor:** {log.get('setor', 'N/A')}")
                            st.markdown(f"**💻 Sistema:** {log.get('sistema', 'N/A')}")
                            st.markdown(f"**📝 Descrição:** {log.get('descricao', 'N/A')}")
                            st.markdown(f"**📞 Canal:** {log.get('canal', 'N/A')}")
                            st.markdown(f"**✅ Desfecho:** {log.get('desfecho', 'N/A')}")
                    
                    elif log.get('tipo') == 'demanda':
                        # Demanda Concluída (ITEM 7)
                        duracao_min = log.get('duracao_minutos', 0)
                        with st.expander(f"📋 #{idx} - Demanda - {colaborador} - {data_hora} ({duracao_min:.0f} min)"):
                            st.markdown(f"**Colaborador:** {colaborador}")
                            st.markdown(f"**📝 Atividade:** {log.get('atividade', 'N/A')}")
                            
                            # Horários
                            inicio = log.get('inicio', '')
                            fim = log.get('fim', '')
                            if inicio:
                                try:
                                    inicio_dt = datetime.fromisoformat(inicio)
                                    st.markdown(f"**🕐 Início:** {inicio_dt.strftime('%d/%m/%Y %H:%M:%S')}")
                                except:
                                    st.markdown(f"**🕐 Início:** {inicio}")
                            
                            if fim:
                                try:
                                    fim_dt = datetime.fromisoformat(fim)
                                    st.markdown(f"**🕐 Fim:** {fim_dt.strftime('%d/%m/%Y %H:%M:%S')}")
                                except:
                                    st.markdown(f"**🕐 Fim:** {fim}")
                            
                            st.markdown(f"**⏱️ Duração:** {duracao_min:.0f} minutos ({duracao_min/60:.1f} horas)")
                    
                    elif 'inicio' in log and 'tempo' in log:
                        # Horas Extras
                        with st.expander(f"⏰ #{idx} - Horas Extras - {colaborador} - {data_hora}"):
                            st.markdown(f"**Colaborador:** {colaborador}")
                            st.markdown(f"**📅 Data:** {log.get('data', 'N/A')}")
                            st.markdown(f"**🕐 Início:** {log.get('inicio', 'N/A')}")
                            st.markdown(f"**⏱️ Tempo Total:** {log.get('tempo', 'N/A')}")
                            st.markdown(f"**📝 Motivo:** {log.get('motivo', 'N/A')}")
                    
                    elif 'titulo' in log and 'relato' in log:
                        # Erro/Novidade
                        with st.expander(f"Bug: #{idx} - Erro/Novidade - {colaborador} - {data_hora}"):
                            st.markdown(f"**👤 Autor:** {colaborador}")
                            st.markdown(f"**📌 Título:** {log.get('titulo', 'N/A')}")
                            st.markdown(f"**🎯 Objetivo:**")
                            st.text(log.get('objetivo', 'N/A'))
                            st.markdown(f"**🧪 Relato:**")
                            st.text(log.get('relato', 'N/A'))
                            st.markdown(f"**🏁 Resultado:**")
                            st.text(log.get('resultado', 'N/A'))
                
                st.markdown("---")
                
                # Botões de ação
                col_a1, col_a2 = st.columns(2)
                
                with col_a1:
                    if st.button("🗑️ Limpar Todos os Registros", use_container_width=True):
                        st.session_state.daily_logs = []
                        st.success("✅ Registros limpos!")
                        time.sleep(1)
                        st.rerun()
                
                with col_a2:
                    # Exportar para HTML
                    if st.button("📥 Gerar Relatório HTML", use_container_width=True):
                        html_content = gerar_html_relatorio(logs_filtrados)
                        
                        # Botão de download
                        st.download_button(
                            label="⬇️ Baixar Relatório HTML",
                            data=html_content,
                            file_name=f"relatorio_informatica_{now_brasilia().strftime('%Y%m%d_%H%M%S')}.html",
                            mime="text/html"
                        )
                        
                        # Exibir preview
                        st.success("✅ Relatório gerado! Clique no botão acima para baixar e abrir em nova aba.")
                        st.info("💡 Dica: Após baixar, clique duas vezes no arquivo .html para abrir no navegador")
    
    # ==================== PAINEL ADMIN BD ====================
    # ==================== PAINEL ADMIN ====================
    elif st.session_state.active_view == "admin_panel":
        if not st.session_state.is_admin:
            st.error("❌ Acesso negado! Apenas administradores.")
        else:
            with st.container(border=True):
                st.markdown("### Painel Administrativo")
                st.caption(f"Admin: {st.session_state.usuario_logado}")
                
                tab1, tab2, tab3 = st.tabs(["Cadastrar Colaborador", "Gerenciar Demandas", "Banco de Dados"])
                
                # TAB 1: Cadastrar Colaborador
                with tab1:
                    st.markdown("#### Adicionar Novo Colaborador")
                    novo_nome = st.text_input("Nome completo:", key="admin_novo_colab")
                    nova_senha = st.text_input("Senha inicial:", type="password", value="user123", key="admin_nova_senha")
                    is_admin_novo = st.checkbox("É administrador?", key="admin_is_admin")
                    
                    if st.button("Adicionar Colaborador", key="btn_add_colab", type="primary"):
                        if novo_nome:
                            from auth_system import adicionar_usuario
                            sucesso = adicionar_usuario(novo_nome, nova_senha, is_admin_novo)
                            if sucesso:
                                # Inicializar estados
                                st.session_state.status_texto[novo_nome] = 'Indisponível'
                                st.session_state.bastao_counts[novo_nome] = 0
                                st.session_state[f'check_{novo_nome}'] = False
                                save_state()
                                st.success(f"✅ {novo_nome} cadastrado com sucesso!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Colaborador já existe no banco de dados!")
                        else:
                            st.warning("⚠️ Digite o nome completo!")
                
                # TAB 2: Gerenciar Demandas
                with tab2:
                    st.markdown("#### Publicar Nova Demanda")
                    nova_demanda_texto = st.text_area("Descrição da demanda:", height=100, key="admin_nova_demanda")
                    
                    col_p1, col_p2 = st.columns(2)
                    
                    with col_p1:
                        prioridade = st.select_slider("Prioridade:", 
                                                     options=["Baixa", "Média", "Alta", "Urgente"],
                                                     value="Média",
                                                     key="admin_prioridade")
                    
                    with col_p2:
                        setor = st.selectbox("Setor:",
                                            options=["Geral", "Cartório", "Gabinete", "Setores Administrativos"],
                                            key="admin_setor")
                    
                    # Direcionar para colaborador específico
                    direcionar = st.checkbox("Direcionar para colaborador específico?", key="admin_direcionar")
                    
                    colaborador_direcionado = None
                    if direcionar:
                        colaboradores_disponiveis = [c for c in COLABORADORES 
                                                    if c in st.session_state.bastao_queue]
                        
                        if colaboradores_disponiveis:
                            colaborador_direcionado = st.selectbox(
                                "Selecione o colaborador:",
                                options=colaboradores_disponiveis,
                                key="admin_colab_direcionado"
                            )
                            st.info(f"A demanda será direcionada para {colaborador_direcionado}")
                        else:
                            st.warning("Nenhum colaborador disponível na fila.")
                            direcionar = False
                    
                    if st.button("Publicar Demanda", key="btn_pub_demanda", type="primary"):
                        if nova_demanda_texto:
                            if 'demandas_publicas' not in st.session_state:
                                st.session_state.demandas_publicas = []
                            
                            # Limpar QUALQUER "arr" do início
                            texto_limpo = nova_demanda_texto.strip()
                            # Remove tudo antes do primeiro colchete [
                            if '[' in texto_limpo and not texto_limpo.startswith('['):
                                texto_limpo = texto_limpo[texto_limpo.index('['):]
                            
                            demanda_obj = {
                                'id': len(st.session_state.demandas_publicas) + 1,
                                'texto': texto_limpo,
                                'prioridade': prioridade,
                                'setor': setor,
                                'criado_em': now_brasilia().isoformat(),
                                'criado_por': st.session_state.usuario_logado,
                                'ativa': True,
                                'direcionada_para': colaborador_direcionado if direcionar else None
                            }
                            st.session_state.demandas_publicas.append(demanda_obj)
                            save_admin_data()
                            
                            # Se direcionada, atribuir automaticamente
                            if colaborador_direcionado:
                                atividade_desc = f"[{setor}] {texto_limpo[:100]}"
                                st.session_state.demanda_start_times[colaborador_direcionado] = now_brasilia()
                                st.session_state.status_texto[colaborador_direcionado] = f"Atividade: {atividade_desc}"
                                
                                if colaborador_direcionado in st.session_state.bastao_queue:
                                    st.session_state.bastao_queue.remove(colaborador_direcionado)
                                st.session_state[f'check_{colaborador_direcionado}'] = False
                                
                                if 'Bastão' in st.session_state.status_texto.get(colaborador_direcionado, ''):
                                    check_and_assume_baton()
                                
                                save_state()
                                st.success(f"✅ Demanda direcionada para {colaborador_direcionado}!")
                            else:
                                st.success("✅ Demanda publicada!")
                            
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.warning("Digite a descrição da demanda!")
                    
                    # Listar demandas ativas
                    st.markdown("---")
                    st.markdown("#### Demandas Ativas")
                    if st.session_state.get('demandas_publicas', []):
                        for dem in st.session_state.demandas_publicas:
                            if dem.get('ativa', True):
                                col1, col2 = st.columns([0.9, 0.1])
                                
                                setor_tag = dem.get('setor', 'Geral')
                                direcionado = dem.get('direcionada_para')
                                
                                texto_exibicao = f"[{setor_tag}] {dem['texto'][:50]}..."
                                if direcionado:
                                    texto_exibicao = f"→ {direcionado}: " + texto_exibicao
                                
                                col1.write(f"**{dem['id']}.** {texto_exibicao}")
                                
                                if col2.button("✕", key=f"del_dem_{dem['id']}"):
                                    dem['ativa'] = False
                                    save_admin_data()
                                    st.rerun()
                    else:
                        st.info("Nenhuma demanda ativa no momento.")
                
                # TAB 3: Banco de Dados
                with tab3:
                    st.markdown("#### Gerenciar Banco de Dados")
                    if st.button("Abrir Painel de BD", use_container_width=True):
                        st.session_state.active_view = 'admin_bd'
                        st.rerun()
    
    # ==================== PAINEL ADMIN BD ====================
    elif st.session_state.active_view == "admin_bd":
        mostrar_painel_admin_bd()

# Coluna lateral (Disponibilidade)
with col_disponibilidade:
    # Pequeno espaço para alinhar com o topo do card do usuário
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    
    st.header('Status dos(as) Colaboradores(as)')
    
    # Listas de status
    import re
    ui_lists = {
        'fila': [],
        'almoco': [],
        'saida': [],
        'ausente': [],
        'atividade_especifica': [],
        'indisponivel': []
    }
    
    for nome in COLABORADORES:
        if nome in st.session_state.bastao_queue:
            ui_lists['fila'].append(nome)
        
        status = st.session_state.status_texto.get(nome, 'Indisponível')
        
        if status == '' or status is None:
            pass
        elif status == 'Almoço':
            ui_lists['almoco'].append(nome)
        elif status == 'Ausente':
            ui_lists['ausente'].append(nome)
        elif status == 'Saída rápida':
            ui_lists['saida'].append(nome)
        elif status == 'Indisponível':
            if nome not in st.session_state.bastao_queue:
                ui_lists['indisponivel'].append(nome)
        
        if 'Atividade:' in status:
            match = re.search(r'Atividade: (.*)', status)
            if match:
                ui_lists['atividade_especifica'].append((nome, match.group(1).split('|')[0].strip()))
    
    # Renderizar fila
    st.subheader(f'✅ Na Fila ({len(ui_lists["fila"])})')
    render_order = [c for c in queue if c in ui_lists["fila"]]
    if not render_order:
        st.caption('Ninguém na fila.')
    else:
        for nome in render_order:
            col_nome, col_check = st.columns([0.85, 0.15], vertical_alignment="center")
            key = f'chk_fila_{nome}'
            # Usar estado persistido do checkbox
            is_checked = st.session_state.get(f'check_{nome}', True)
            col_check.checkbox(' ', key=key, value=is_checked, on_change=toggle_queue, args=(nome,), label_visibility='collapsed')
            
            status_atual = st.session_state.status_texto.get(nome, '')
            extra_info = ""
            if "Atividade" in status_atual:
                extra_info += " 📋"
            
            if nome == responsavel:
                display = f'<span style="background-color: #FFD700; color: #000; padding: 2px 6px; border-radius: 5px; font-weight: bold;">{nome}</span>'
            else:
                display = f'**{nome}**{extra_info} :blue-background[Aguardando]'
            col_nome.markdown(display, unsafe_allow_html=True)
    st.markdown('---')
    
    # Função auxiliar para renderizar seções
    def render_section_detalhada(title, icon, lista_tuplas, tag_color, keyword_removal):
        st.subheader(f'{icon} {title} ({len(lista_tuplas)})')
        if not lista_tuplas:
            st.caption(f'Ninguém em {title.lower()}.')
        else:
            for nome, desc in sorted(lista_tuplas, key=lambda x: x[0]):
                col_nome, col_btn = st.columns([0.7, 0.3], vertical_alignment="center")
                
                col_nome.markdown(f'**{nome}**', unsafe_allow_html=True)
                col_nome.caption(desc)
                
                # PROBLEMA 4: Mostrar horário de início E tempo decorrido
                if nome in st.session_state.get('demanda_start_times', {}):
                    start_time = st.session_state.demanda_start_times[nome]
                    if isinstance(start_time, str):
                        start_time = datetime.fromisoformat(start_time)
                    
                    # Horário de início
                    horario_inicio = start_time.strftime('%H:%M')
                    
                    # Tempo decorrido
                    elapsed = now_brasilia() - start_time
                    elapsed_mins = int(elapsed.total_seconds() / 60)
                    
                    col_nome.caption(f"🕐 Início: {horario_inicio} | ⏱️ {elapsed_mins} min")
                
                # Botão Finalizar (ITEM 1)
                if col_btn.button("✅", key=f"fim_{nome}_{title}", help="Finalizar"):
                    finalizar_demanda(nome)
        st.markdown('---')
    
    def render_section_simples(title, icon, names, tag_color):
        st.subheader(f'{icon} {title} ({len(names)})')
        if not names:
            st.caption(f'Ninguém em {title.lower()}.')
        else:
            for nome in sorted(names):
                # Proporção 70/30 para dar mais espaço ao checkbox
                col_nome, col_check = st.columns([0.70, 0.30], vertical_alignment="center")
                key_dummy = f'chk_simples_{title}_{nome}'
                
                col_nome.markdown(f'**{nome}**')
                
                # Mostrar horário de saída para almoço (ITEM 4)
                if title == 'Almoço' and nome in st.session_state.get('almoco_times', {}):
                    saida_time = st.session_state.almoco_times[nome]
                    if isinstance(saida_time, str):
                        saida_time = datetime.fromisoformat(saida_time)
                    col_nome.caption(f"🕐 Saiu: {saida_time.strftime('%H:%M')}")
                
                # Checkbox - estilos globais aplicados via CSS
                col_check.checkbox('', key=key_dummy, 
                                 value=(False if title == 'Indisponível' else True),
                                 on_change=(enter_from_indisponivel if title == 'Indisponível' 
                                          else leave_specific_status),
                                 args=((nome,) if title == 'Indisponível' else (nome, title)),
                                 label_visibility='collapsed')
        st.markdown('---')
    
    render_section_detalhada('Em Demanda', '📋', ui_lists['atividade_especifica'], 'orange', 'Atividade')
    render_section_simples('Almoço', '🍽️', ui_lists['almoco'], 'red')
    render_section_simples('Saída rápida', '🚶', ui_lists['saida'], 'red')
    render_section_simples('Ausente', '👤', ui_lists['ausente'], 'violet')
    render_section_simples('Indisponível', '❌', ui_lists['indisponivel'], 'grey')

# Footer
st.markdown("---")
st.caption("Sistema de Controle de Bastão - Informática 2026 - Versão Local (Sem Integrações Externas)")
