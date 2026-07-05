import sqlite3
import hashlib
import streamlit as st
from pathlib import Path
import time

DB_PATH = Path("bastao_users.db")
LOGIN_ATTEMPTS = {}

def rate_limit_login(username, max_attempts=5, window=300):
    now = time.time()
    if username not in LOGIN_ATTEMPTS:
        LOGIN_ATTEMPTS[username] = []
    LOGIN_ATTEMPTS[username] = [t for t in LOGIN_ATTEMPTS[username] if now - t < window]
    if len(LOGIN_ATTEMPTS[username]) >= max_attempts:
        tempo_restante = int(window - (now - LOGIN_ATTEMPTS[username][0]))
        return False, tempo_restante
    LOGIN_ATTEMPTS[username].append(now)
    return True, 0

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

_USE_POSTGRES = None

def _usar_postgres():
    global _USE_POSTGRES
    if _USE_POSTGRES is not None:
        return _USE_POSTGRES
    try:
        _USE_POSTGRES = (
            hasattr(st, "secrets")
            and "postgres" in st.secrets
            and bool(st.secrets["postgres"].get("url") or st.secrets["postgres"].get("host"))
        )
    except Exception:
        _USE_POSTGRES = False
    return _USE_POSTGRES

def get_connection():
    if _usar_postgres():
        import psycopg2
        pg = st.secrets["postgres"]
        if pg.get("url"):
            return psycopg2.connect(pg["url"], sslmode="require")
        return psycopg2.connect(
            host=pg["host"],
            port=pg.get("port", 5432),
            dbname=pg["dbname"],
            user=pg["user"],
            password=pg["password"],
            sslmode=pg.get("sslmode", "require"),
        )
    return sqlite3.connect(DB_PATH)

def _q(query):
    if _usar_postgres():
        return query.replace("?", "%s")
    return query

def _pk():
    return "SERIAL PRIMARY KEY" if _usar_postgres() else "INTEGER PRIMARY KEY AUTOINCREMENT"

def init_database():
    try:
        usando_pg = _usar_postgres()
        print(f"INFO: backend = {(chr(10)) + (39*chr(61))} PostgreSQL PERSISTENTE" if usando_pg else "INFO: backend = SQLite local (filesystem efemero)")

        conn = get_connection()
        c = conn.cursor()

        c.execute(f'''
            CREATE TABLE IF NOT EXISTS usuarios (
                id {_pk()},
                username TEXT UNIQUE,
                nome TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0,
                ativo INTEGER DEFAULT 1,
                primeiro_acesso INTEGER DEFAULT 1,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        c.execute("SELECT COUNT(*) FROM usuarios")
        count = c.fetchone()[0]
        print(f"INFO: usuarios no banco = {count}")

        if count == 0:
            try:
                if hasattr(st, "secrets") and "database" in st.secrets:
                    force_change = st.secrets["database"].get("force_password_change", True)
                else:
                    force_change = True
                primeiro_acesso_valor = 1 if force_change else 0
            except Exception:
                primeiro_acesso_valor = 1

            usuarios_iniciais = [
                ("rungue",   "Álvaro Rungue",                         "admin123", 1),
                ("field90",  "Daniely Cristina Cunha Mesquita",       "admin123", 1),
                ("field240", "Celso Daniel Vilano Cardoso",           "admin123", 1),
                ("field284", "Cinthia Mery Facion",                   "admin123", 1),
                ("field255", "Igor Eduardo Martins",                   "admin123", 1),
                ("field273", "Leonardo Gonçalves Fleury",             "admin123", 1),
                ("field17",  "Marcio Rodrigues Alves",                "admin123", 1),
                ("field155", "Pollyanna Silva Pereira",               "admin123", 1),
                ("field249", "Rôner Ribeiro Júnior",                  "admin123", 1),
                ("marcelo",  "Marcelo dos Santos Dutra",              "admin123", 1),
                ("field108", "Frederico Augusto Costa Gonçalves",     "user123",  0),
                ("field153", "Judson Heleno Faleiro",                 "user123",  0),
                ("field186", "Marcelo Batista Amaral",                "user123",  0),
                ("field199", "Otávio Reis",                           "user123",  0),
                ("field178", "Ramon Shander de Almeida",              "user123",  0),
                ("field41",  "Rodrigo Marinho Marques",               "user123",  0),
                ("field111", "Warley Roberto de Oliveira Cruz",       "user123",  0),
            ]

            for username, nome, senha, is_admin in usuarios_iniciais:
                senha_hash = hash_password(senha)
                try:
                    c.execute(
                        _q("INSERT INTO usuarios (username, nome, senha_hash, is_admin, primeiro_acesso) VALUES (?, ?, ?, ?, ?)"),
                        (username, nome, senha_hash, is_admin, primeiro_acesso_valor)
                    )
                except Exception:
                    if usando_pg:
                        conn.rollback()

        conn.commit()
        conn.close()

        if usando_pg:
            print("OK: PostgreSQL conectado - senhas persistentes!")
        else:
            print("AVISO: SQLite local - senhas podem resetar em restarts")

    except Exception as e:
        print(f"ERRO init_database: {e}")

def verificar_login(nome, senha):
    pode_tentar, tempo_restante = rate_limit_login(nome)
    if not pode_tentar:
        m, s = tempo_restante // 60, tempo_restante % 60
        return {"bloqueado": True, "mensagem": f"Muitas tentativas. Tente em {m}min {s}s"}
    try:
        conn = get_connection()
        c = conn.cursor()
        senha_hash = hash_password(senha)
        c.execute(
            _q("""SELECT id, username, nome, is_admin, ativo, primeiro_acesso
               FROM usuarios WHERE (username = ? OR nome = ?) AND senha_hash = ?"""),
            (nome, nome, senha_hash)
        )
        resultado = c.fetchone()
        conn.close()
        if resultado and resultado[4]:
            return {
                "id": resultado[0],
                "username": resultado[1],
                "nome": resultado[2],
                "is_admin": bool(resultado[3]),
                "ativo": bool(resultado[4]),
                "primeiro_acesso": bool(resultado[5])
            }
    except Exception as e:
        print(f"ERRO verificar_login: {e}")
    return None

def listar_usuarios_ativos():
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT nome FROM usuarios WHERE ativo = 1 ORDER BY nome")
        usuarios = [row[0] for row in c.fetchall()]
        conn.close()
        return usuarios
    except Exception as e:
        print(f"ERRO listar_usuarios: {e}")
        return []

def adicionar_usuario(username, nome, senha, is_admin=False):
    try:
        conn = get_connection()
        c = conn.cursor()
        senha_hash = hash_password(senha)
        c.execute(
            _q("INSERT INTO usuarios (username, nome, senha_hash, is_admin, primeiro_acesso) VALUES (?, ?, ?, ?, 1)"),
            (username, nome, senha_hash, 1 if is_admin else 0)
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def remover_usuario(nome):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute(_q("DELETE FROM usuarios WHERE nome = ?"), (nome,))
        conn.commit()
        afetadas = c.rowcount
        conn.close()
        return afetadas > 0
    except Exception:
        return False

def desativar_usuario(nome):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute(_q("UPDATE usuarios SET ativo = 0 WHERE nome = ?"), (nome,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def alterar_senha(nome, senha_nova):
    try:
        conn = get_connection()
        c = conn.cursor()
        senha_hash = hash_password(senha_nova)
        c.execute(
            _q("UPDATE usuarios SET senha_hash = ?, primeiro_acesso = 0 WHERE nome = ?"),
            (senha_hash, nome)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"ERRO alterar_senha: {e}")

def is_usuario_admin(nome):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute(_q("SELECT is_admin FROM usuarios WHERE nome = ? AND ativo = 1"), (nome,))
        resultado = c.fetchone()
        conn.close()
        return bool(resultado[0]) if resultado else False
    except Exception:
        return False
