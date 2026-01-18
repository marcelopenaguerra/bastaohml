import streamlit as st
from auth_system import init_database, verificar_login, listar_usuarios_ativos

def mostrar_tela_login():
    """Exibe tela de login"""
    
    # CSS da tela de login
    st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 2rem;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .login-title {
            text-align: center;
            color: #0f172a;
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .login-subtitle {
            text-align: center;
            color: #64748b;
            font-size: 0.875rem;
            margin-bottom: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Container centralizado
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="login-container">
            <div class="login-title">🥂 Controle de Bastão</div>
            <div class="login-subtitle">Setor de Informática • TJMG • 2026</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🔐 Login")
        
        # Formulário de login
        with st.form("login_form", clear_on_submit=False):
            nome = st.selectbox(
                "Colaborador(a):",
                options=["Selecione..."] + listar_usuarios_ativos(),
                key="login_nome"
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
                    - Colaboradores: `senha123`
                    
                    Altere sua senha após o primeiro login!
                    """)
        
        # Processar login
        if login_button:
            if nome == "Selecione...":
                st.error("❌ Selecione um colaborador!")
            elif not senha:
                st.error("❌ Digite sua senha!")
            else:
                usuario = verificar_login(nome, senha)
                
                if usuario:
                    # Login bem-sucedido
                    st.session_state.logged_in = True
                    st.session_state.usuario_logado = usuario['nome']
                    st.session_state.is_admin = usuario['is_admin']
                    st.session_state.user_id = usuario['id']
                    
                    st.success(f"✅ Bem-vindo(a), {usuario['nome']}!")
                    st.rerun()
                else:
                    st.error("❌ Credenciais inválidas!")
        
        # Rodapé
        st.markdown("---")
        st.caption("🔒 Sistema seguro com autenticação de usuários")

def verificar_autenticacao():
    """Verifica se usuário está autenticado"""
    if not st.session_state.get('logged_in', False):
        mostrar_tela_login()
        st.stop()

def fazer_logout():
    """Faz logout do usuário"""
    st.session_state.logged_in = False
    st.session_state.usuario_logado = None
    st.session_state.is_admin = False
    st.session_state.user_id = None
    st.rerun()
