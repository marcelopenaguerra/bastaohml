import sqlite3
import hashlib
import streamlit as st
from pathlib import Path

# Caminho do banco de dados
DB_PATH = Path("bastao_users.db")

def hash_password(password):
    """Hash de senha com SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_database():
    """Inicializa banco de dados de usuários"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Tabela de usuários
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Verificar se já tem usuários
    c.execute("SELECT COUNT(*) FROM usuarios")
    count = c.fetchone()[0]
    
    if count == 0:
        # Criar admins iniciais
        admins = [
            ("Daniely Cristina Cunha Mesquita", "admin123"),
            ("Marcio Rodrigues Alves", "admin123"),
            ("Leonardo goncalves fleury", "admin123")
        ]
        
        for nome, senha in admins:
            senha_hash = hash_password(senha)
            c.execute(
                "INSERT INTO usuarios (nome, senha_hash, is_admin) VALUES (?, ?, 1)",
                (nome, senha_hash)
            )
        
        # Criar colaboradores regulares
        colaboradores = [
            "Frederico Augusto Costa Gonçalves",
            "Ramon Shander de Almeida",
            "Marcelo Batista Amaral",
            "Rodrigo Marinho Marques",
            "Otávio Reis",
            "Judson Heleno Faleiro",
            "Roner Ribeiro Júnior",
            "Warley Roberto de Oliveira Cruz",
            "Igor Eduardo Martins",
            "Marcelo dos Santos Dutra",
            "Celso Daniel Vilano Cardoso",
            "Pollyanna Silva Pereira",
            "Cinthia Mery Facion"
        ]
        
        for nome in colaboradores:
            senha_hash = hash_password("senha123")  # Senha padrão inicial
            c.execute(
                "INSERT INTO usuarios (nome, senha_hash, is_admin) VALUES (?, ?, 0)",
                (nome, senha_hash)
            )
    
    conn.commit()
    conn.close()

def verificar_login(nome, senha):
    """Verifica credenciais e retorna dados do usuário"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    senha_hash = hash_password(senha)
    c.execute(
        "SELECT id, nome, is_admin, ativo FROM usuarios WHERE nome = ? AND senha_hash = ?",
        (nome, senha_hash)
    )
    
    resultado = c.fetchone()
    conn.close()
    
    if resultado and resultado[3]:  # Se encontrou e está ativo
        return {
            'id': resultado[0],
            'nome': resultado[1],
            'is_admin': bool(resultado[2]),
            'ativo': bool(resultado[3])
        }
    return None

def listar_usuarios_ativos():
    """Lista todos os usuários ativos"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT nome FROM usuarios WHERE ativo = 1 ORDER BY nome")
    usuarios = [row[0] for row in c.fetchall()]
    conn.close()
    return usuarios

def adicionar_usuario(nome, senha, is_admin=False):
    """Adiciona novo usuário"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        senha_hash = hash_password(senha)
        c.execute(
            "INSERT INTO usuarios (nome, senha_hash, is_admin) VALUES (?, ?, ?)",
            (nome, senha_hash, 1 if is_admin else 0)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False  # Usuário já existe

def remover_usuario(nome):
    """Desativa usuário (soft delete)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE usuarios SET ativo = 0 WHERE nome = ?", (nome,))
    conn.commit()
    conn.close()

def alterar_senha(nome, senha_nova):
    """Altera senha do usuário"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    senha_hash = hash_password(senha_nova)
    c.execute("UPDATE usuarios SET senha_hash = ? WHERE nome = ?", (senha_hash, nome))
    conn.commit()
    conn.close()

def is_usuario_admin(nome):
    """Verifica se usuário é admin"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT is_admin FROM usuarios WHERE nome = ? AND ativo = 1", (nome,))
    resultado = c.fetchone()
    conn.close()
    return bool(resultado[0]) if resultado else False
