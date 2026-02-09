“””
Sistema de Estado Compartilhado
Garante que todos os usuários vejam o mesmo estado em tempo real
“””

import json
import streamlit as st
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import threading
import time

# Arquivos de persistência

STATE_FILE = Path(“bastao_state.json”)
ADMIN_FILE = Path(“admin_data.json”)
LOCK_FILE = Path(”.state.lock”)

# Lock para evitar condições de corrida

_file_lock = threading.Lock()

class SharedState:
“”“Gerenciador de estado compartilhado entre todas as sessões”””

```
@staticmethod
def load_from_disk() -> Dict[str, Any]:
    """Carrega estado do disco - SEMPRE pega a versão mais recente"""
    with _file_lock:
        try:
            if STATE_FILE.exists():
                data = json.loads(STATE_FILE.read_text())
                
                # Converter strings ISO para datetime
                if data.get('bastao_start_time'):
                    try:
                        data['bastao_start_time'] = datetime.fromisoformat(data['bastao_start_time'])
                    except:
                        data['bastao_start_time'] = None
                
                # Converter almoco_times
                almoco_times = data.get('almoco_times', {})
                data['almoco_times'] = {
                    k: datetime.fromisoformat(v) if isinstance(v, str) else v 
                    for k, v in almoco_times.items()
                }
                
                # Converter demanda_start_times
                demanda_times = data.get('demanda_start_times', {})
                data['demanda_start_times'] = {
                    k: datetime.fromisoformat(v) if isinstance(v, str) else v 
                    for k, v in demanda_times.items()
                }
                
                return data
        except Exception as e:
            print(f"Erro ao carregar estado: {e}")
    
    # Retornar estado vazio se falhar
    return SharedState._get_empty_state()

@staticmethod
def save_to_disk(data: Dict[str, Any]):
    """Salva estado no disco - TODAS as sessões compartilham este arquivo"""
    with _file_lock:
        try:
            # Converter datetime para string ISO
            save_data = data.copy()
            
            if isinstance(save_data.get('bastao_start_time'), datetime):
                save_data['bastao_start_time'] = save_data['bastao_start_time'].isoformat()
            
            # Converter almoco_times
            almoco_times = save_data.get('almoco_times', {})
            save_data['almoco_times'] = {
                k: v.isoformat() if isinstance(v, datetime) else v 
                for k, v in almoco_times.items()
            }
            
            # Converter demanda_start_times
            demanda_times = save_data.get('demanda_start_times', {})
            save_data['demanda_start_times'] = {
                k: v.isoformat() if isinstance(v, datetime) else v 
                for k, v in demanda_times.items()
            }
            
            STATE_FILE.write_text(json.dumps(save_data, default=str, ensure_ascii=False, indent=2))
            return True
        except Exception as e:
            print(f"Erro ao salvar estado: {e}")
            return False

@staticmethod
def _get_empty_state() -> Dict[str, Any]:
    """Retorna estado vazio padrão"""
    return {
        'bastao_queue': [],
        'status_texto': {},
        'bastao_start_time': None,
        'bastao_counts': {},
        'simon_ranking': [],
        'daily_logs': [],
        'checks': {},
        'almoco_times': {},
        'demanda_start_times': {},
        'demanda_logs': []
    }

@staticmethod
def sync_to_session_state():
    """
    SINCRONIZA do disco para st.session_state
    Chame isto ANTES de renderizar qualquer coisa
    """
    disk_data = SharedState.load_from_disk()
    
    # Atualizar session_state com dados do disco
    st.session_state.bastao_queue = disk_data.get('bastao_queue', [])
    st.session_state.status_texto = disk_data.get('status_texto', {})
    st.session_state.bastao_start_time = disk_data.get('bastao_start_time')
    st.session_state.bastao_counts = disk_data.get('bastao_counts', {})
    st.session_state.simon_ranking = disk_data.get('simon_ranking', [])
    st.session_state.daily_logs = disk_data.get('daily_logs', [])
    st.session_state.almoco_times = disk_data.get('almoco_times', {})
    st.session_state.demanda_start_times = disk_data.get('demanda_start_times', {})
    st.session_state.demanda_logs = disk_data.get('demanda_logs', [])
    
    # Restaurar checkboxes
    for nome, val in disk_data.get('checks', {}).items():
        st.session_state[f'check_{nome}'] = val

@staticmethod
def sync_from_session_state():
    """
    SINCRONIZA de st.session_state para o disco
    Chame isto DEPOIS de qualquer mudança
    """
    # Coletar dados do session_state
    data = {
        'bastao_queue': st.session_state.get('bastao_queue', []),
        'status_texto': st.session_state.get('status_texto', {}),
        'bastao_start_time': st.session_state.get('bastao_start_time'),
        'bastao_counts': st.session_state.get('bastao_counts', {}),
        'simon_ranking': st.session_state.get('simon_ranking', []),
        'daily_logs': st.session_state.get('daily_logs', []),
        'almoco_times': st.session_state.get('almoco_times', {}),
        'demanda_start_times': st.session_state.get('demanda_start_times', {}),
        'demanda_logs': st.session_state.get('demanda_logs', [])
    }
    
    # Coletar checkboxes
    checks = {}
    for key in st.session_state.keys():
        if key.startswith('check_'):
            checks[key.replace('check_', '')] = st.session_state[key]
    data['checks'] = checks
    
    # Salvar no disco
    SharedState.save_to_disk(data)

@staticmethod
def load_admin_data():
    """Carrega dados administrativos"""
    with _file_lock:
        try:
            if ADMIN_FILE.exists():
                data = json.loads(ADMIN_FILE.read_text())
                st.session_state.colaboradores_extras = data.get('colaboradores_extras', [])
                st.session_state.demandas_publicas = data.get('demandas_publicas', [])
                return True
        except:
            pass
    return False

@staticmethod
def save_admin_data():
    """Salva dados administrativos"""
    with _file_lock:
        try:
            data = {
                'colaboradores_extras': st.session_state.get('colaboradores_extras', []),
                'demandas_publicas': st.session_state.get('demandas_publicas', [])
            }
            ADMIN_FILE.write_text(json.dumps(data, default=str, ensure_ascii=False, indent=2))
            return True
        except:
            return False
```

# Funções de conveniência para compatibilidade

def load_state():
“”“Carrega estado compartilhado (compatibilidade)”””
SharedState.sync_to_session_state()
return True

def save_state():
“”“Salva estado compartilhado (compatibilidade)”””
SharedState.sync_from_session_state()

def load_admin_data():
“”“Carrega dados admin (compatibilidade)”””
return SharedState.load_admin_data()

def save_admin_data():
“”“Salva dados admin (compatibilidade)”””
return SharedState.save_admin_data()