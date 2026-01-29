#!/usr/bin/env python3
"""
Script de Atualização de Permissões
Atualiza is_admin de acordo com a lista oficial
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("bastao_users.db")

# Lista oficial de permissões
ADMINS = [
    "rungue",
    "field90",
    "field240",
    "field284",
    "field255",
    "field273",
    "field17",
    "field155",
    "field249",
    "marcelo"
]

COLABORADORES = [
    "field108",
    "field153",
    "field186",
    "field199",
    "field178",
    "field41",
    "field111"
]

def atualizar_permissoes():
    """Atualiza permissões de admin/colaborador no banco"""
    
    if not DB_PATH.exists():
        print("❌ Banco de dados não encontrado!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Verificar se coluna username existe
    c.execute("PRAGMA table_info(usuarios)")
    columns = [col[1] for col in c.fetchall()]
    
    if 'username' not in columns:
        print("❌ Banco ainda não tem coluna 'username'. Execute o sistema primeiro para fazer a migração.")
        conn.close()
        return
    
    print("📊 Atualizando permissões...")
    print()
    
    # Atualizar ADMINS
    print("👑 ADMINS:")
    for username in ADMINS:
        c.execute("SELECT nome FROM usuarios WHERE username = ?", (username,))
        result = c.fetchone()
        
        if result:
            nome = result[0]
            c.execute("UPDATE usuarios SET is_admin = 1 WHERE username = ?", (username,))
            print(f"  ✅ {username:12} → {nome} (ADMIN)")
        else:
            print(f"  ⚠️ {username:12} → NÃO ENCONTRADO NO BANCO")
    
    print()
    print("👤 COLABORADORES:")
    for username in COLABORADORES:
        c.execute("SELECT nome FROM usuarios WHERE username = ?", (username,))
        result = c.fetchone()
        
        if result:
            nome = result[0]
            c.execute("UPDATE usuarios SET is_admin = 0 WHERE username = ?", (username,))
            print(f"  ✅ {username:12} → {nome} (COLABORADOR)")
        else:
            print(f"  ⚠️ {username:12} → NÃO ENCONTRADO NO BANCO")
    
    # Verificar se há outros usuários
    print()
    print("🔍 Verificando outros usuários...")
    c.execute("""
        SELECT username, nome, is_admin 
        FROM usuarios 
        WHERE username NOT IN (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ADMINS + COLABORADORES)
    
    outros = c.fetchall()
    if outros:
        print("⚠️ USUÁRIOS NÃO MAPEADOS:")
        for username, nome, is_admin in outros:
            tipo = "ADMIN" if is_admin else "COLABORADOR"
            print(f"  {username:12} → {nome} ({tipo})")
        print("  ℹ️ Estes usuários NÃO foram alterados.")
    else:
        print("✅ Todos os usuários estão mapeados!")
    
    conn.commit()
    conn.close()
    
    print()
    print("=" * 60)
    print("✅ ATUALIZAÇÃO CONCLUÍDA!")
    print("=" * 60)
    print()
    print("Resumo:")
    print(f"  - {len(ADMINS)} admins configurados")
    print(f"  - {len(COLABORADORES)} colaboradores configurados")
    print()
    print("Próximos passos:")
    print("  1. Reiniciar o sistema")
    print("  2. Testar login com usuários admin e colaborador")
    print("  3. Verificar que permissões estão corretas")

if __name__ == "__main__":
    atualizar_permissoes()
