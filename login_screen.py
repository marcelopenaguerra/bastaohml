import streamlit as st
from auth_system import verificar_login, listar_usuarios_ativos, alterar_senha
import hashlib
import secrets
import time

# ==================== SISTEMA DE TOKENS SEGUROS ====================
# Gera tokens únicos por sessão que expiram
SESSION_TOKENS = {}  # {token: {'usuario': nome, 'expira': timestamp}}
TOKEN_DURACAO = 28800  # 8 horas (jornada de trabalho)

def gerar_token_seguro(usuario_nome):
    """Gera token único e seguro para o usuário"""
    # Token = hash(usuario + timestamp + secret)
    secret = secrets.token_hex(32)
    timestamp = str(time.time())
    token_raw = f"{usuario_nome}{timestamp}{secret}"
    token = hashlib.sha256(token_raw.encode()).hexdigest()[:32]
    
    # Guardar token com expiração
    SESSION_TOKENS[token] = {
        'usuario': usuario_nome,
        'expira': time.time() + TOKEN_DURACAO,
        'criado': time.time()
    }
    
    return token

def validar_token(token):
    """Valida token e retorna usuário se válido"""
    if token not in SESSION_TOKENS:
        return None
    
    token_data = SESSION_TOKENS[token]
    
    # Verificar expiração
    if time.time() > token_data['expira']:
        del SESSION_TOKENS[token]
        return None
    
    # RENOVAÇÃO AUTOMÁTICA: Se faltam menos de 1 hora, renovar por mais 8 horas
    tempo_restante = token_data['expira'] - time.time()
    if tempo_restante < 3600:  # Menos de 1 hora restante
        SESSION_TOKENS[token]['expira'] = time.time() + TOKEN_DURACAO
        # print(f"🔄 Token renovado para {token_data['usuario']} (+ 8 horas)")
    
    return token_data['usuario']

def limpar_tokens_expirados():
    """Remove tokens expirados"""
    tokens_para_remover = []
    for token, data in SESSION_TOKENS.items():
        if time.time() > data['expira']:
            tokens_para_remover.append(token)
    
    for token in tokens_para_remover:
        del SESSION_TOKENS[token]

def mostrar_tela_troca_senha():
    """Tela obrigatória de troca de senha no primeiro acesso"""
    st.markdown("""
    <div style='background: #fef3c7; padding: 1rem; border-radius: 8px; border-left: 4px solid #f59e0b; margin-bottom: 1rem;'>
        <strong>⚠️ PRIMEIRO ACESSO</strong><br>
        Por segurança, você deve alterar sua senha antes de continuar.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔑 Alterar Senha")
    
    with st.form("form_trocar_senha_obrigatoria"):
        senha_atual = st.text_input("Senha atual:", type="password")
        nova_senha = st.text_input("Nova senha:", type="password", help="Mínimo 6 caracteres")
        confirmar = st.text_input("Confirme a nova senha:", type="password")
        
        if st.form_submit_button("✅ Alterar Senha", type="primary", use_container_width=True):
            if not senha_atual or not nova_senha or not confirmar:
                st.error("❌ Preencha todos os campos!")
            elif nova_senha != confirmar:
                st.error("❌ As senhas não conferem!")
            elif len(nova_senha) < 6:
                st.error("❌ A senha deve ter pelo menos 6 caracteres!")
            else:
                # Verificar senha atual
                usuario = verificar_login(st.session_state.usuario_logado, senha_atual)
                if usuario:
                    alterar_senha(st.session_state.usuario_logado, nova_senha)
                    st.session_state.precisa_trocar_senha = False
                    st.success("✅ Senha alterada com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Senha atual incorreta!")

def mostrar_tela_login():
    """Tela de login principal"""
    st.markdown("""
    <style>
    .login-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    }
    .login-title {
        color: white;
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .login-subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown("""
        <div class="login-container">
            <div class="login-title">🥂 Controle de Bastão</div>
            <div class="login-subtitle">Setor de Informática • TJMG • 2026</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🔐 Login")
        
        # Formulário de login COM USERNAME
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(
                "Usuário/ID:",
                placeholder="Ex: field90, rungue, marcelo...",
                help="Digite seu username (field90) ou nome completo",
                key="login_username"
            )
            
            senha = st.text_input(
                "Senha:",
                type="password",
                key="login_senha"
            )
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                login_button = st.form_submit_button(
                    "🔓 Entrar",
                    use_container_width=True,
                    type="primary"
                )
            
            with col_btn2:
                if st.form_submit_button("❓ Ajuda", use_container_width=True):
                    st.info("""
                    **Primeira vez?**
                    
                    Senhas padrão:
                    - Admins: `admin123`
                    - Colaboradores: `user123`
                    
                    Use seu username (Ex: field90, rungue) ou nome completo para fazer login.
                    
                    Altere sua senha após o primeiro login!
                    """)
        
        # Processar login
        if login_button:
            if not username:
                st.error("❌ Digite seu usuário/ID!")
            elif not senha:
                st.error("❌ Digite sua senha!")
            else:
                usuario = verificar_login(username, senha)
                
                # Verificar se está bloqueado por rate limiting
                if usuario and usuario.get('bloqueado'):
                    st.error(f"🔒 {usuario['mensagem']}")
                elif usuario:
                    # Login bem-sucedido
                    st.session_state.logged_in = True
                    st.session_state.usuario_logado = usuario['nome']
                    st.session_state.is_admin = usuario['is_admin']
                    st.session_state.user_id = usuario['id']
                    st.session_state.precisa_trocar_senha = usuario['primeiro_acesso']
                    
                    # CRÍTICO: Gerar token seguro único
                    token = gerar_token_seguro(usuario['nome'])
                    st.session_state.auth_token = token
                    st.query_params['token'] = token
                    
                    st.success(f"✅ Bem-vindo(a), {usuario['nome']}!")
                    st.rerun()
                else:
                    st.error("❌ Credenciais inválidas!")
        
        # Rodapé
        st.markdown("---")
        st.caption("🔒 Sistema seguro com autenticação de usuários")

def verificar_autenticacao():
    """Verifica se usuário está autenticado - COM TOKEN SEGURO"""
    # Limpar tokens expirados
    limpar_tokens_expirados()
    
    # Se já está logado nesta sessão, verificar se token ainda é válido
    if st.session_state.get('logged_in', False):
        token = st.session_state.get('auth_token')
        if token:
            usuario_validado = validar_token(token)
            if not usuario_validado:
                # Token expirado - forçar logout
                st.session_state.logged_in = False
                st.session_state.usuario_logado = None
                st.warning("⚠️ Sessão expirada. Faça login novamente.")
                mostrar_tela_login()
                st.stop()
            elif usuario_validado != st.session_state.usuario_logado:
                # Token válido mas usuário diferente - erro crítico
                st.error("❌ Erro de autenticação. Faça login novamente.")
                st.session_state.logged_in = False
                mostrar_tela_login()
                st.stop()
            # Token válido - continuar (com renovação automática já feita em validar_token)
        else:
            # Sem token mas marcado como logado - inconsistência
            st.session_state.logged_in = False
            mostrar_tela_login()
            st.stop()
    
    # Tentar restaurar sessão da URL (APENAS SE TOKEN VÁLIDO)
    if not st.session_state.get('logged_in', False):
        if 'token' in st.query_params:
            token = st.query_params['token']
            usuario_nome = validar_token(token)
            
            if usuario_nome:
                # Token válido - restaurar sessão
                from auth_system import is_usuario_admin, get_connection, _q

                # CRÍTICO: Buscar primeiro_acesso do banco (não assumir False)
                conn = get_connection()
                c = conn.cursor()
                c.execute(_q("SELECT primeiro_acesso FROM usuarios WHERE nome = ?"), (usuario_nome,))
                resultado = c.fetchone()
                conn.close()

                precisa_trocar = bool(resultado[0]) if resultado else False
                
                st.session_state.logged_in = True
                st.session_state.usuario_logado = usuario_nome
                st.session_state.is_admin = is_usuario_admin(usuario_nome)
                st.session_state.auth_token = token
                st.session_state.precisa_trocar_senha = precisa_trocar  # ← Usar valor real do banco
            else:
                # Token inválido - limpar e mostrar login
                if 'token' in st.query_params:
                    del st.query_params['token']
                st.warning("⚠️ Sessão inválida ou expirada.")
                mostrar_tela_login()
                st.stop()
    
    if not st.session_state.get('logged_in', False):
        mostrar_tela_login()
        st.stop()
    
    # Se precisa trocar senha, mostrar tela
    if st.session_state.get('precisa_trocar_senha', False):
        mostrar_tela_troca_senha()
        st.stop()

def fazer_logout():
    """Faz logout do usuário - LIMPA TOKEN"""
    # Invalidar token
    token = st.session_state.get('auth_token')
    if token and token in SESSION_TOKENS:
        del SESSION_TOKENS[token]
    
    # Limpar query params
    if 'token' in st.query_params:
        del st.query_params['token']
    
    # Limpar apenas dados de login
    st.session_state.logged_in = False
    st.session_state.usuario_logado = None
    st.session_state.is_admin = False
    st.session_state.user_id = None
    st.session_state.auth_token = None
    st.session_state.precisa_trocar_senha = False
    
    # Resetar flag de entrada na fila
    if 'ja_processou_entrada_fila' in st.session_state:
        st.session_state.ja_processou_entrada_fila = False
    
    st.rerun()
