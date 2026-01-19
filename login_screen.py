import streamlit as st
from auth_system import verificar_login, listar_usuarios_ativos, alterar_senha

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
                    - Colaboradores: `user123`
                    
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
                    st.session_state.precisa_trocar_senha = usuario['primeiro_acesso']
                    
                    # CRÍTICO: Adicionar token na URL para persistir sessão
                    st.query_params['user'] = usuario['nome']
                    
                    st.success(f"✅ Bem-vindo(a), {usuario['nome']}!")
                    st.rerun()
                else:
                    st.error("❌ Credenciais inválidas!")
        
        # Rodapé
        st.markdown("---")
        st.caption("🔒 Sistema seguro com autenticação de usuários")

def verificar_autenticacao():
    """Verifica se usuário está autenticado - COM PERSISTÊNCIA"""
    # Tentar restaurar sessão de query params
    if not st.session_state.get('logged_in', False):
        # Verificar se há token na URL
        if 'user' in st.query_params:
            usuario_nome = st.query_params['user']
            # Restaurar sessão
            from auth_system import verificar_login, listar_usuarios_ativos
            usuarios = listar_usuarios_ativos()
            if usuario_nome in usuarios:
                # Recriar sessão sem senha (já estava logado)
                st.session_state.logged_in = True
                st.session_state.usuario_logado = usuario_nome
                # Buscar info do usuário no banco
                from auth_system import is_usuario_admin
                st.session_state.is_admin = is_usuario_admin(usuario_nome)
                st.session_state.precisa_trocar_senha = False
    
    if not st.session_state.get('logged_in', False):
        mostrar_tela_login()
        st.stop()
    
    # Se precisa trocar senha, mostrar tela
    if st.session_state.get('precisa_trocar_senha', False):
        mostrar_tela_troca_senha()
        st.stop()

def fazer_logout():
    """Faz logout do usuário - SIMPLES!"""
    # Limpar query params
    if 'user' in st.query_params:
        del st.query_params['user']
    
    # Limpar apenas dados de login
    st.session_state.logged_in = False
    st.session_state.usuario_logado = None
    st.session_state.is_admin = False
    st.session_state.user_id = None
    st.session_state.precisa_trocar_senha = False
    st.rerun()
