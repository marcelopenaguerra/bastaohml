import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from auth_system import hash_password, DB_PATH

def mostrar_painel_admin_bd():
“”“Painel administrativo do banco de dados”””

```
if not st.session_state.get('is_admin', False):
    st.error("❌ Acesso negado! Apenas administradores podem acessar este painel.")
    return

st.markdown("## 🗄️ Administração do Banco de Dados")

# Verificar se banco existe
if not DB_PATH.exists():
    st.warning("⚠️ Banco de dados ainda não foi criado!")
    return

# Tabs do painel
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
    
    conn = sqlite3.connect(DB_PATH)
    
    # Carregar usuários
    df_usuarios = pd.read_sql_query("""
        SELECT 
            id,
            nome,
            CASE WHEN is_admin = 1 THEN '👑 Admin' ELSE '👤 Colaborador' END as tipo,
            CASE WHEN ativo = 1 THEN '✅ Ativo' ELSE '❌ Inativo' END as status,
            datetime(criado_em, 'localtime') as criado_em
        FROM usuarios
        ORDER BY is_admin DESC, nome
    """, conn)
    
    conn.close()
    
    # Exibir tabela
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
    
    # Adicionar novo usuário
    st.markdown("---")
    st.markdown("### ➕ Adicionar Novo Usuário")
    
    with st.form("form_novo_usuario"):
        col1, col2 = st.columns(2)
        
        with col1:
            novo_nome = st.text_input("Nome completo:")
            nova_senha = st.text_input("Senha inicial:", type="password")
        
        with col2:
            is_admin_novo = st.checkbox("É administrador?")
            st.caption("⚠️ Administradores podem gerenciar usuários e demandas")
        
        if st.form_submit_button("➕ Criar Usuário", type="primary", use_container_width=True):
            if novo_nome and nova_senha:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    senha_hash = hash_password(nova_senha)
                    c.execute(
                        "INSERT INTO usuarios (nome, senha_hash, is_admin) VALUES (?, ?, ?)",
                        (novo_nome, senha_hash, 1 if is_admin_novo else 0)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Usuário '{novo_nome}' criado com sucesso!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("❌ Este usuário já existe!")
            else:
                st.warning("⚠️ Preencha todos os campos!")
    
    # Desativar usuário
    st.markdown("---")
    st.markdown("### 🚫 Desativar Usuário")
    
    conn = sqlite3.connect(DB_PATH)
    usuarios_ativos = pd.read_sql_query(
        "SELECT nome FROM usuarios WHERE ativo = 1 ORDER BY nome", 
        conn
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
                # Verificar se não é o próprio admin
                if usuario_desativar == st.session_state.usuario_logado:
                    st.error("❌ Você não pode desativar sua própria conta!")
                else:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("UPDATE usuarios SET ativo = 0 WHERE nome = ?", (usuario_desativar,))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Usuário '{usuario_desativar}' desativado!")
                    st.rerun()

# ==================== TAB 2: RESETAR SENHAS ====================
with tab2:
    st.markdown("### 🔑 Resetar Senhas de Usuários")
    
    st.info("ℹ️ Use esta função para resetar a senha de usuários que esqueceram suas credenciais.")
    
    conn = sqlite3.connect(DB_PATH)
    usuarios_todos = pd.read_sql_query(
        "SELECT nome FROM usuarios WHERE ativo = 1 ORDER BY nome", 
        conn
    )
    conn.close()
    
    with st.form("form_resetar_senha"):
        usuario_reset = st.selectbox(
            "Selecione o usuário:",
            options=["Selecione..."] + list(usuarios_todos['nome'])
        )
        
        nova_senha_reset = st.text_input(
            "Nova senha:",
            type="password",
            help="Digite a nova senha para este usuário"
        )
        
        confirmar_senha = st.text_input(
            "Confirme a nova senha:",
            type="password"
        )
        
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
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                senha_hash = hash_password(nova_senha_reset)
                c.execute(
                    "UPDATE usuarios SET senha_hash = ? WHERE nome = ?",
                    (senha_hash, usuario_reset)
                )
                conn.commit()
                conn.close()
                st.success(f"✅ Senha de '{usuario_reset}' resetada com sucesso!")
                st.info(f"🔐 Nova senha: `{nova_senha_reset}`")

# ==================== TAB 3: ESTATÍSTICAS ====================
with tab3:
    st.markdown("### 📊 Estatísticas do Banco de Dados")
    
    conn = sqlite3.connect(DB_PATH)
    
    # Estatísticas gerais
    stats = pd.read_sql_query("""
        SELECT 
            COUNT(*) as total_usuarios,
            SUM(CASE WHEN ativo = 1 THEN 1 ELSE 0 END) as usuarios_ativos,
            SUM(CASE WHEN ativo = 0 THEN 1 ELSE 0 END) as usuarios_inativos,
            SUM(CASE WHEN is_admin = 1 THEN 1 ELSE 0 END) as admins,
            SUM(CASE WHEN is_admin = 0 THEN 1 ELSE 0 END) as colaboradores
        FROM usuarios
    """, conn)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total", stats['total_usuarios'][0])
    
    with col2:
        st.metric("✅ Ativos", stats['usuarios_ativos'][0])
    
    with col3:
        st.metric("❌ Inativos", stats['usuarios_inativos'][0])
    
    with col4:
        st.metric("👑 Admins", stats['admins'][0])
    
    with col5:
        st.metric("👤 Colaboradores", stats['colaboradores'][0])
    
    # Gráfico de tipo de usuário
    st.markdown("---")
    st.markdown("#### Distribuição de Usuários")
    
    tipo_dist = pd.read_sql_query("""
        SELECT 
            CASE WHEN is_admin = 1 THEN 'Administradores' ELSE 'Colaboradores' END as tipo,
            COUNT(*) as quantidade
        FROM usuarios
        WHERE ativo = 1
        GROUP BY is_admin
    """, conn)
    
    st.bar_chart(tipo_dist.set_index('tipo'))
    
    # Usuários criados recentemente
    st.markdown("---")
    st.markdown("#### 🆕 Últimos 5 Usuários Criados")
    
    ultimos = pd.read_sql_query("""
        SELECT 
            nome,
            CASE WHEN is_admin = 1 THEN '👑 Admin' ELSE '👤 Colaborador' END as tipo,
            datetime(criado_em, 'localtime') as criado_em
        FROM usuarios
        ORDER BY criado_em DESC
        LIMIT 5
    """, conn)
    
    st.dataframe(ultimos, use_container_width=True, hide_index=True)
    
    conn.close()

# ==================== TAB 4: BACKUP ====================
with tab4:
    st.markdown("### 💾 Backup do Banco de Dados")
    
    st.info("ℹ️ Faça backup regularmente para não perder os dados!")
    
    # Informações do banco
    tamanho_kb = DB_PATH.stat().st_size / 1024
    st.metric("Tamanho do Banco", f"{tamanho_kb:.2f} KB")
    
    # Botão de download
    with open(DB_PATH, 'rb') as f:
        st.download_button(
            label="⬇️ Baixar Backup do Banco de Dados",
            data=f,
            file_name=f"bastao_users_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            mime="application/x-sqlite3",
            use_container_width=True,
            type="primary"
        )
    
    st.markdown("---")
    st.markdown("### 📤 Exportar Usuários (CSV)")
    
    conn = sqlite3.connect(DB_PATH)
    df_export = pd.read_sql_query("""
        SELECT 
            nome,
            CASE WHEN is_admin = 1 THEN 'Admin' ELSE 'Colaborador' END as tipo,
            CASE WHEN ativo = 1 THEN 'Ativo' ELSE 'Inativo' END as status,
            criado_em
        FROM usuarios
        ORDER BY nome
    """, conn)
    conn.close()
    
    csv = df_export.to_csv(index=False)
    
    st.download_button(
        label="⬇️ Baixar Lista de Usuários (CSV)",
        data=csv,
        file_name=f"usuarios_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )

# ==================== TAB 5: SQL DIRETO ====================
with tab5:
    st.markdown("### 📋 Executar SQL Personalizado")
    
    st.warning("⚠️ **ATENÇÃO:** Use com cuidado! Comandos SQL incorretos podem danificar o banco!")
    
    sql_query = st.text_area(
        "Query SQL:",
        height=150,
        placeholder="SELECT * FROM usuarios WHERE ativo = 1;",
        help="Digite uma query SQL SELECT para consultar o banco"
    )
    
    if st.button("▶️ Executar Query", type="primary"):
        if sql_query.strip():
            # Validar que é apenas SELECT
            if not sql_query.strip().upper().startswith('SELECT'):
                st.error("❌ Apenas queries SELECT são permitidas por segurança!")
            else:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    resultado = pd.read_sql_query(sql_query, conn)
                    conn.close()
                    
                    st.success(f"✅ Query executada! {len(resultado)} resultado(s)")
                    st.dataframe(resultado, use_container_width=True)
                    
                    # Opção de download
                    csv = resultado.to_csv(index=False)
                    st.download_button(
                        "⬇️ Baixar Resultado (CSV)",
                        csv,
                        f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv"
                    )
                except Exception as e:
                    st.error(f"❌ Erro ao executar query: {str(e)}")
        else:
            st.warning("⚠️ Digite uma query SQL!")
    
    # Queries úteis sugeridas
    st.markdown("---")
    st.markdown("#### 💡 Queries Úteis")
    
    with st.expander("📖 Ver Exemplos de Queries"):
        st.code("""
```

– Listar todos os usuários ativos
SELECT * FROM usuarios WHERE ativo = 1;

– Contar admins e colaboradores
SELECT
CASE WHEN is_admin = 1 THEN ‘Admin’ ELSE ‘Colaborador’ END as tipo,
COUNT(*) as quantidade
FROM usuarios
WHERE ativo = 1
GROUP BY is_admin;

– Usuários criados nos últimos 7 dias
SELECT nome, criado_em
FROM usuarios
WHERE date(criado_em) >= date(‘now’, ‘-7 days’)
ORDER BY criado_em DESC;

– Verificar duplicatas (não deveria ter)
SELECT nome, COUNT(*)
FROM usuarios
GROUP BY nome
HAVING COUNT(*) > 1;
“””, language=“sql”)

# Adicionar ao menu lateral admin

def adicionar_menu_bd_sidebar():
“”“Adiciona opção de BD no menu admin da sidebar”””
if st.session_state.get(‘is_admin’, False):
with st.sidebar:
st.markdown(”—”)
if st.button(“🗄️ Gerenciar Banco de Dados”, use_container_width=True):
st.session_state.active_view = ‘admin_bd’