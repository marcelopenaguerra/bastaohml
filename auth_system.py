import sqlite3
import hashlib
import streamlit as st
from pathlib import Path
import time

# Caminho do banco de dados

DB_PATH = Path(“bastao_users.db”)

# Sistema de Rate Limiting (proteção contra brute force)

LOGIN_ATTEMPTS = {}  # {username: [timestamp1, timestamp2, …]}

def rate_limit_login(username, max_attempts=5, window=300):
“””
Limita tentativas de login a 5 por 5 minutos

```
Args:
    username: Nome do usuário
    max_attempts: Máximo de tentativas permitidas (padrão: 5)
    window: Janela de tempo em segundos (padrão: 300 = 5 minutos)

Returns:
    bool: True se pode tentar, False se bloqueado
"""
now = time.time()

if username not in LOGIN_ATTEMPTS:
    LOGIN_ATTEMPTS[username] = []

# Limpar tentativas antigas (fora da janela)
LOGIN_ATTEMPTS[username] = [
    t for t in LOGIN_ATTEMPTS[username] 
    if now - t < window
]

# Verificar se excedeu limite
if len(LOGIN_ATTEMPTS[username]) >= max_attempts:
    tempo_restante = int(window - (now - LOGIN_ATTEMPTS[username][0]))
    return False, tempo_restante

# Registrar tentativa
LOGIN_ATTEMPTS[username].append(now)
return True, 0
```

def hash_password(password):
“”“Hash de senha com SHA-256”””
return hashlib.sha256(password.encode()).hexdigest()

# REMOVIDO: salvar_sessao, carregar_sessao, limpar_sessao

# Sessão agora é APENAS no st.session_state (não compartilha entre usuários)

def init_database():
“”“Inicializa banco de dados de usuários”””
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

```
# Verificar se tabela existe
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
table_exists = c.fetchone() is not None

if table_exists:
    # MIGRAÇÃO: Verificar se coluna username existe
    c.execute("PRAGMA table_info(usuarios)")
    columns = [column[1] for column in c.fetchall()]
    
    if 'username' not in columns:
        # MIGRAÇÃO NECESSÁRIA: Adicionar coluna username
        print("⚠️ MIGRAÇÃO: Adicionando coluna 'username' ao banco existente...")
        
        try:
            # Adicionar coluna username
            c.execute("ALTER TABLE usuarios ADD COLUMN username TEXT")
            
            # Atualizar usernames baseado nos nomes existentes
            # Mapeamento de nomes para usernames
            username_map = {
                "Álvaro Rungue": "rungue",
                "Daniely Cristina Cunha Mesquita": "field90",
                "Celso Daniel Vilano Cardoso": "field240",
                "Cinthia Mery Facion": "field284",
                "Igor Eduardo Martins": "field255",
                "Leonardo Gonçalves Fleury": "field273",
                "Leonardo goncalves fleury": "field273",  # Variante
                "Marcio Rodrigues Alves": "field17",
                "Pollyanna Silva Pereira": "field155",
                "Rôner Ribeiro Júnior": "field249",
                "Roner Ribeiro Júnior": "field249",  # Variante
                "Marcelo dos Santos Dutra": "marcelo",
                "Frederico Augusto Costa Gonçalves": "field108",
                "Judson Heleno Faleiro": "field153",
                "Marcelo Batista Amaral": "field186",
                "Otávio Reis": "field199",
                "Ramon Shander de Almeida": "field178",
                "Rodrigo Marinho Marques": "field41",
                "Warley Roberto de Oliveira Cruz": "field111",
            }
            
            # Buscar todos os usuários existentes
            c.execute("SELECT id, nome FROM usuarios")
            usuarios_existentes = c.fetchall()
            
            # Atualizar cada usuário com seu username
            for user_id, nome in usuarios_existentes:
                username = username_map.get(nome)
                if username:
                    c.execute("UPDATE usuarios SET username = ? WHERE id = ?", (username, user_id))
                else:
                    # Se não encontrar no mapa, gerar username genérico
                    username_gerado = f"user{user_id}"
                    c.execute("UPDATE usuarios SET username = ? WHERE id = ?", (username_gerado, user_id))
                    print(f"⚠️ Username genérico criado para '{nome}': {username_gerado}")
            
            # Tornar username UNIQUE e NOT NULL
            # SQLite não permite ALTER COLUMN, então criar índice UNIQUE
            c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_username ON usuarios(username)")
            
            conn.commit()
            print("✅ MIGRAÇÃO concluída com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro na migração: {e}")
            conn.rollback()

# Criar tabela se não existir
c.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        nome TEXT UNIQUE NOT NULL,
        senha_hash TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0,
        ativo INTEGER DEFAULT 1,
        primeiro_acesso INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Verificar se já tem usuários
c.execute("SELECT COUNT(*) FROM usuarios")
count = c.fetchone()[0]

if count == 0:
    # Criar usuários com username (ID) conforme lista fornecida
    usuarios_iniciais = [
        # (username, nome, senha, is_admin)
        ("rungue", "Álvaro Rungue", "admin123", 1),
        ("field90", "Daniely Cristina Cunha Mesquita", "admin123", 1),
        ("field240", "Celso Daniel Vilano Cardoso", "admin123", 1),
        ("field284", "Cinthia Mery Facion", "admin123", 1),
        ("field255", "Igor Eduardo Martins", "admin123", 1),
        ("field273", "Leonardo Gonçalves Fleury", "admin123", 1),
        ("field17", "Marcio Rodrigues Alves", "admin123", 1),
        ("field155", "Pollyanna Silva Pereira", "admin123", 1),
        ("field249", "Rôner Ribeiro Júnior", "admin123", 1),
        ("marcelo", "Marcelo dos Santos Dutra", "admin123", 1),
        ("field108", "Frederico Augusto Costa Gonçalves", "user123", 0),
        ("field153", "Judson Heleno Faleiro", "user123", 0),
        ("field186", "Marcelo Batista Amaral", "user123", 0),
        ("field199", "Otávio Reis", "user123", 0),
        ("field178", "Ramon Shander de Almeida", "user123", 0),
        ("field41", "Rodrigo Marinho Marques", "user123", 0),
        ("field111", "Warley Roberto de Oliveira Cruz", "user123", 0),
    ]
    
    for username, nome, senha, is_admin in usuarios_iniciais:
        senha_hash = hash_password(senha)
        c.execute(
            "INSERT INTO usuarios (username, nome, senha_hash, is_admin, primeiro_acesso) VALUES (?, ?, ?, ?, 1)",
            (username, nome, senha_hash, is_admin)
        )

conn.commit()
conn.close()
```

def verificar_login(nome, senha):
“””
Verifica credenciais e retorna dados do usuário
SEGURANÇA: Rate limiting de 5 tentativas por 5 minutos
“””
# RATE LIMITING: Verificar se usuário não está bloqueado
pode_tentar, tempo_restante = rate_limit_login(nome)
if not pode_tentar:
minutos = tempo_restante // 60
segundos = tempo_restante % 60
return {
‘bloqueado’: True,
‘mensagem’: f”Muitas tentativas. Tente novamente em {minutos}min {segundos}s”
}

```
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

senha_hash = hash_password(senha)

# Buscar por USERNAME ou NOME
c.execute(
    """SELECT id, username, nome, is_admin, ativo, primeiro_acesso 
       FROM usuarios 
       WHERE (username = ? OR nome = ?) AND senha_hash = ?""",
    (nome, nome, senha_hash)
)

resultado = c.fetchone()
conn.close()

if resultado and resultado[4]:  # Se encontrou e está ativo
    return {
        'id': resultado[0],
        'username': resultado[1],
        'nome': resultado[2],  # NOME COMPLETO para exibição
        'is_admin': bool(resultado[3]),
        'ativo': bool(resultado[4]),
        'primeiro_acesso': bool(resultado[5])
    }
return None
```

def listar_usuarios_ativos():
“”“Lista todos os usuários ativos”””
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute(“SELECT nome FROM usuarios WHERE ativo = 1 ORDER BY nome”)
usuarios = [row[0] for row in c.fetchall()]
conn.close()
return usuarios

def adicionar_usuario(username, nome, senha, is_admin=False):
“””
Adiciona novo usuário com USERNAME
Args:
username: ID/username (field90, rungue, etc)
nome: Nome completo
senha: Senha inicial
is_admin: Se é administrador
“””
try:
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
senha_hash = hash_password(senha)
c.execute(
“INSERT INTO usuarios (username, nome, senha_hash, is_admin, primeiro_acesso) VALUES (?, ?, ?, ?, 1)”,
(username, nome, senha_hash, 1 if is_admin else 0)
)
conn.commit()
conn.close()
return True
except sqlite3.IntegrityError:
return False  # Usuário já existe

def remover_usuario(nome):
“”“Remove usuário permanentemente do banco (DELETE real)”””
try:
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute(“DELETE FROM usuarios WHERE nome = ?”, (nome,))
conn.commit()
linhas_afetadas = c.rowcount
conn.close()
return linhas_afetadas > 0
except Exception as e:
return False

def desativar_usuario(nome):
“”“Desativa usuário sem remover do banco (soft delete)”””
try:
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute(“UPDATE usuarios SET ativo = 0 WHERE nome = ?”, (nome,))
conn.commit()
conn.close()
return True
except Exception as e:
return False

def alterar_senha(nome, senha_nova):
“”“Altera senha do usuário e marca que não é mais primeiro acesso”””
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
senha_hash = hash_password(senha_nova)
c.execute(
“UPDATE usuarios SET senha_hash = ?, primeiro_acesso = 0 WHERE nome = ?”,
(senha_hash, nome)
)
conn.commit()
conn.close()

def is_usuario_admin(nome):
“”“Verifica se usuário é admin”””
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute(“SELECT is_admin FROM usuarios WHERE nome = ? AND ativo = 1”, (nome,))
resultado = c.fetchone()
conn.close()
return bool(resultado[0]) if resultado else False