#!/usr/bin/env python3
"""Script para limpar prefixos 'arr' de demandas antigas"""

import json

# Carregar admin_data.json
try:
    with open('admin_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print("❌ Arquivo admin_data.json não encontrado")
    exit(1)

# Limpar demandas
if 'demandas_publicas' in data:
    demandas = data['demandas_publicas']
    limpas = 0
    
    for dem in demandas:
        texto_original = dem.get('texto', '')
        texto_limpo = texto_original.strip()
        
        # Remover todas as variações de "arr" no início (loop até limpar tudo)
        while texto_limpo.startswith(('arr[', 'arr', '.arr', '_arr')):
            if texto_limpo.startswith('arr['):
                texto_limpo = texto_limpo[3:]
            elif texto_limpo.startswith(('.arr', '_arr')):
                texto_limpo = texto_limpo[4:]
            elif texto_limpo.startswith('arr'):
                texto_limpo = texto_limpo[3:]
            texto_limpo = texto_limpo.strip()
        
        if texto_original != texto_limpo:
            limpas += 1
            dem['texto'] = texto_limpo
    
    # Salvar
    with open('admin_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {limpas} demandas limpas com sucesso!")
    print(f"📊 Total de demandas: {len(demandas)}")
else:
    print("⚠️ Nenhuma demanda encontrada")
