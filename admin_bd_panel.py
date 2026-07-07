import streamlit as st
import pandas as pd
from datetime import datetime
from auth_system import hash_password, get_connection, _q, _usar_postgres

def _read_sql(query, conn):
    """pd.read_sql compatível com SQLite e psycopg2"""
    try:
        # Tenta direto (funciona com SQLite)
        return pd.read_sql_query(query, conn)
    except Exception:
        # Fallback para psycopg2: usa cursor manualmente
        cursor = conn.cursor()
        cursor.execute(query)
        cols = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        return pd.DataFrame(rows, columns=cols)

def mostrar_painel_admin_bd():
    """Painel administrativo do banco de dados"""

    if not st.session_state.get('is_admin', False):
        st.error("❌ Acesso negado! Apenas administradores podem acessar este painel.")
        return

    st.markdown("## 🗄️ Administração do Banco de Dados")

    backend = "☁️ PostgreSQL (Supabase)" if _usar_postgres() else "💾 SQLite local"
    st.caption(f"Backend: **{backend}**")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👥 Usuários",
        "🔑 Resetar Senhas",
        "📊 Estatísticas",
        "💾 Backup",
        "📋 SQL Direto"
    ])

    # ==================== TAB 1: USUÁRIOS ====================
    with tab1:
        st.markdown("### 👥 Lista de Usuários")

        try:
            conn = get_connection()
            df_usuarios = _read_sql("""
                SELECT
                    id,
                    nome,
                    CASE WHEN is_admin = 1 THEN '👑 Admin' ELSE '👤 Colaborador' END as tipo,
                    CASE WHEN ativo = 1 THEN '✅ Ativo' ELSE '❌ Inativo' END as status,
                    criado_em
                FROM usuarios
                ORDER BY is_admin DESC, nome
            """, conn)
            conn.close()

            st.dataframe(
                df_usuarios,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": "ID",
                    "nome": st.column_config.TextColumn("Nome", width="large"),
                    "tipo": "Tipo",
                    "status": "Status",
                    "criado_em": "Criado em"
                }
            )
            st.markdown(f"**Total:** {len(df_usuarios)} usuários")
        except Exception as e:
            st.error(f"Erro ao carregar usuários: {e}")

        st.markdown("---")
        st.markdown("### ➕ Adicionar Novo Usuário")

        with st.form("form_novo_usuario"):
            col1, col2 = st.columns(2)
            with col1:
                novo_username = st.text_input("Username (ID):", placeholder="ex: field200")
                novo_nome = st.text_input("Nome completo:")
                nova_senha = st.text_input("Senha inicial:", type="password")
            with col2:
                is_admin_novo = st.checkbox("É administrador?")
                st.caption("⚠️ Administradores podem gerenciar usuários e demandas")

            if st.form_submit_button("➕ Criar Usuário", type="primary", use_container_width=True):
                if novo_username and novo_nome and nova_senha:
                    try:
                        conn = get_connection()
                        c = conn.cursor()
                        senha_hash = hash_password(nova_senha)
                        c.execute(
                            _q("INSERT INTO usuarios (username, nome, senha_hash, is_admin, primeiro_acesso) VALUES (?, ?, ?, ?, 1)"),
                            (novo_username, novo_nome, senha_hash, 1 if is_admin_novo else 0)
                        )
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Usuário '{novo_nome}' criado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro: {e}")
                else:
                    st.warning("⚠️ Preencha todos os campos!")

        st.markdown("---")
        st.markdown("### 🚫 Desativar Usuário")

        try:
            conn = get_connection()
            usuarios_ativos = _read_sql(
                "SELECT nome FROM usuarios WHERE ativo = 1 ORDER BY nome", conn
            )
            conn.close()

            col1, col2 = st.columns([3, 1])
            with col1:
                usuario_desativar = st.selectbox(
                    "Selecione usuário para desativar:",
                    options=["Selecione..."] + list(usuarios_ativos['nome'])
                )
            with col2:
                if st.button("🚫 Desativar", type="secondary", use_container_width=True):
                    if usuario_desativar != "Selecione...":
                        if usuario_desativar == st.session_state.usuario_logado:
                            st.error("❌ Você não pode desativar sua própria conta!")
                        else:
                            conn = get_connection()
                            c = conn.cursor()
                            c.execute(_q("UPDATE usuarios SET ativo = 0 WHERE nome = ?"), (usuario_desativar,))
                            conn.commit()
                            conn.close()
                            st.success(f"✅ Usuário '{usuario_desativar}' desativado!")
                            st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")

    # ==================== TAB 2: RESETAR SENHAS ====================
    with tab2:
        st.markdown("### 🔑 Resetar Senhas de Usuários")
        st.info("ℹ️ Use esta função para resetar a senha de usuários que esqueceram suas credenciais.")

        try:
            conn = get_connection()
            usuarios_todos = _read_sql(
                "SELECT nome FROM usuarios WHERE ativo = 1 ORDER BY nome", conn
            )
            conn.close()

            with st.form("form_resetar_senha"):
                usuario_reset = st.selectbox(
                    "Selecione o usuário:",
                    options=["Selecione..."] + list(usuarios_todos['nome'])
                )
                nova_senha_reset = st.text_input("Nova senha:", type="password")
                confirmar_senha = st.text_input("Confirme a nova senha:", type="password")

                if st.form_submit_button("🔑 Resetar Senha", type="primary", use_container_width=True):
                    if usuario_reset == "Selecione...":
                        st.warning("⚠️ Selecione um usuário!")
                    elif not nova_senha_reset or not confirmar_senha:
                        st.warning("⚠️ Preencha todos os campos!")
                    elif nova_senha_reset != confirmar_senha:
                        st.error("❌ As senhas não conferem!")
                    elif len(nova_senha_reset) < 6:
                        st.error("❌ A senha deve ter pelo menos 6 caracteres!")
                    else:
                        conn = get_connection()
                        c = conn.cursor()
                        senha_hash = hash_password(nova_senha_reset)
                        c.execute(
                            _q("UPDATE usuarios SET senha_hash = ?, primeiro_acesso = 0 WHERE nome = ?"),
                            (senha_hash, usuario_reset)
                        )
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Senha de '{usuario_reset}' resetada com sucesso!")
                        st.info(f"🔐 Nova senha: `{nova_senha_reset}`")
        except Exception as e:
            st.error(f"Erro: {e}")

    # ==================== TAB 3: ESTATÍSTICAS ====================
    with tab3:
        st.markdown("### 📊 Estatísticas do Banco de Dados")

        try:
            conn = get_connection()

            stats = _read_sql("""
                SELECT
                    COUNT(*) as total_usuarios,
                    SUM(CASE WHEN ativo = 1 THEN 1 ELSE 0 END) as usuarios_ativos,
                    SUM(CASE WHEN ativo = 0 THEN 1 ELSE 0 END) as usuarios_inativos,
                    SUM(CASE WHEN is_admin = 1 THEN 1 ELSE 0 END) as admins,
                    SUM(CASE WHEN is_admin = 0 THEN 1 ELSE 0 END) as colaboradores
                FROM usuarios
            """, conn)

            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Total", stats['total_usuarios'][0])
            col2.metric("✅ Ativos", stats['usuarios_ativos'][0])
            col3.metric("❌ Inativos", stats['usuarios_inativos'][0])
            col4.metric("👑 Admins", stats['admins'][0])
            col5.metric("👤 Colaboradores", stats['colaboradores'][0])

            st.markdown("---")
            tipo_dist = _read_sql("""
                SELECT
                    CASE WHEN is_admin = 1 THEN 'Administradores' ELSE 'Colaboradores' END as tipo,
                    COUNT(*) as quantidade
                FROM usuarios WHERE ativo = 1
                GROUP BY is_admin
            """, conn)
            st.bar_chart(tipo_dist.set_index('tipo'))

            st.markdown("---")
            st.markdown("#### 🆕 Últimos 5 Usuários Criados")
            ultimos = _read_sql("""
                SELECT nome,
                    CASE WHEN is_admin = 1 THEN '👑 Admin' ELSE '👤 Colaborador' END as tipo,
                    criado_em
                FROM usuarios
                ORDER BY criado_em DESC
                LIMIT 5
            """, conn)
            st.dataframe(ultimos, use_container_width=True, hide_index=True)
            conn.close()
        except Exception as e:
            st.error(f"Erro: {e}")

    # ==================== TAB 4: BACKUP ====================
    with tab4:
        st.markdown("### 💾 Backup / Exportar Usuários")

        if _usar_postgres():
            st.info("☁️ Usando PostgreSQL (Supabase). O backup completo do banco é feito diretamente no painel do Supabase em **Database → Backups**.")
        else:
            st.info("💾 Usando SQLite local.")

        st.markdown("### 📤 Exportar Usuários (CSV)")
        try:
            conn = get_connection()
            df_export = _read_sql("""
                SELECT
                    nome,
                    CASE WHEN is_admin = 1 THEN 'Admin' ELSE 'Colaborador' END as tipo,
                    CASE WHEN ativo = 1 THEN 'Ativo' ELSE 'Inativo' END as status,
                    criado_em
                FROM usuarios ORDER BY nome
            """, conn)
            conn.close()

            csv = df_export.to_csv(index=False)
            st.download_button(
                label="⬇️ Baixar Lista de Usuários (CSV)",
                data=csv,
                file_name=f"usuarios_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary"
            )
        except Exception as e:
            st.error(f"Erro ao exportar: {e}")

    # ==================== TAB 5: SQL DIRETO ====================
    with tab5:
        st.markdown("### 📋 Executar SQL Personalizado")
        st.warning("⚠️ **ATENÇÃO:** Use com cuidado! Apenas queries SELECT são permitidas.")

        sql_query = st.text_area(
            "Query SQL:",
            height=150,
            placeholder="SELECT * FROM usuarios WHERE ativo = 1;",
        )

        if st.button("▶️ Executar Query", type="primary"):
            if sql_query.strip():
                if not sql_query.strip().upper().startswith('SELECT'):
                    st.error("❌ Apenas queries SELECT são permitidas por segurança!")
                else:
                    try:
                        conn = get_connection()
                        resultado = _read_sql(sql_query, conn)
                        conn.close()
                        st.success(f"✅ {len(resultado)} resultado(s)")
                        st.dataframe(resultado, use_container_width=True)
                        csv = resultado.to_csv(index=False)
                        st.download_button(
                            "⬇️ Baixar (CSV)", csv,
                            f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            "text/csv"
                        )
                    except Exception as e:
                        st.error(f"❌ Erro: {e}")
            else:
                st.warning("⚠️ Digite uma query SQL!")

        st.markdown("---")
        st.markdown("#### 💡 Queries Úteis")
        with st.expander("📖 Ver Exemplos"):
            st.code("""
-- Listar todos os usuários ativos
SELECT * FROM usuarios WHERE ativo = 1;

-- Contar admins e colaboradores
SELECT
    CASE WHEN is_admin = 1 THEN 'Admin' ELSE 'Colaborador' END as tipo,
    COUNT(*) as quantidade
FROM usuarios WHERE ativo = 1
GROUP BY is_admin;

-- Verificar duplicatas
SELECT nome, COUNT(*)
FROM usuarios
GROUP BY nome
HAVING COUNT(*) > 1;
            """, language="sql")

def adicionar_menu_bd_sidebar():
    """Adiciona opção de BD no menu admin da sidebar"""
    if st.session_state.get('is_admin', False):
        with st.sidebar:
            st.markdown("---")
            if st.button("🗄️ Gerenciar Banco de Dados", use_container_width=True):
                st.session_state.active_view = 'admin_bd'
