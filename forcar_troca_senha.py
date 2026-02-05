#!/usr/bin/env python3
"""
Script para FORÇAR troca de senha de TODOS os usuários existentes
Executa UMA VEZ para atualizar banco de dados
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("bastao_users.db")

def forcar_troca_senha_todos():
    """Marca TODOS os usuários como primeiro_acesso = 1"""
    
    if not DB_PATH.exists():
        print("❌ Banco de dados não encontrado!")
        print(f"   Procurando em: {DB_PATH.absolute()}")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Verificar se coluna primeiro_acesso existe
        c.execute("PRAGMA table_info(usuarios)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'primeiro_acesso' not in columns:
            print("⚠️ Coluna 'primeiro_acesso' não existe. Adicionando...")
            c.execute("ALTER TABLE usuarios ADD COLUMN primeiro_acesso INTEGER DEFAULT 1")
            conn.commit()
            print("✅ Coluna 'primeiro_acesso' adicionada!")
        
        # Contar usuários antes
        c.execute("SELECT COUNT(*) FROM usuarios")
        total = c.fetchone()[0]
        
        print(f"\n📊 Total de usuários no banco: {total}")
        
        # Verificar quantos já precisam trocar senha
        c.execute("SELECT COUNT(*) FROM usuarios WHERE primeiro_acesso = 1")
        ja_marcados = c.fetchone()[0]
        
        print(f"   Já marcados para trocar senha: {ja_marcados}")
        print(f"   Não marcados: {total - ja_marcados}")
        
        if ja_marcados == total:
            print("\n✅ Todos os usuários já estão marcados para trocar senha!")
            return True
        
        # Atualizar TODOS para primeiro_acesso = 1
        c.execute("UPDATE usuarios SET primeiro_acesso = 1")
        conn.commit()
        
        # Verificar resultado
        c.execute("SELECT COUNT(*) FROM usuarios WHERE primeiro_acesso = 1")
        atualizados = c.fetchone()[0]
        
        print(f"\n✅ SUCESSO! {atualizados} usuários marcados para trocar senha!")
        print("\n📋 Lista de usuários que precisarão trocar senha:")
        
        # Listar todos os usuários
        c.execute("SELECT username, nome, is_admin FROM usuarios ORDER BY nome")
        usuarios = c.fetchall()
        
        for username, nome, is_admin in usuarios:
            tipo = "Admin" if is_admin else "Colaborador"
            print(f"   • {nome} (@{username}) - {tipo}")
        
        conn.close()
        
        print("\n" + "="*70)
        print("🔒 PRÓXIMO LOGIN: Todos os usuários DEVERÃO trocar a senha!")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False

if __name__ == "__main__":
    print("="*70)
    print("🔐 FORÇAR TROCA DE SENHA - TODOS OS USUÁRIOS")
    print("="*70)
    print()
    
    sucesso = forcar_troca_senha_todos()
    
    if sucesso:
        print("\n✅ Script executado com sucesso!")
        print("\n💡 PRÓXIMOS PASSOS:")
        print("   1. Reinicie o aplicativo Streamlit")
        print("   2. Todos os usuários verão tela de troca de senha")
        print("   3. Após trocar, poderão usar o sistema normalmente")
    else:
        print("\n❌ Falha na execução. Verifique os erros acima.")
    
    print()
