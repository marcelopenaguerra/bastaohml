"""
Sistema de Estado Compartilhado
Garante que todos os usuários vejam o mesmo estado em tempo real
"""

import json
import streamlit as st
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import threading
import time

from auth_system import _usar_postgres, get_connection, _q

# Arquivos de persistência (usados apenas quando o Postgres não está configurado)
STATE_FILE = Path("bastao_state.json")
ADMIN_FILE = Path("admin_data.json")
LOCK_FILE = Path(".state.lock")

# Lock para evitar condições de corrida
_file_lock = threading.Lock()

class SharedState:
    """Gerenciador de estado compartilhado entre todas as sessões"""

    @staticmethod
    def init_db():
        """Cria a tabela de estado no Postgres (Supabase), se configurado"""
        if not _usar_postgres():
            return
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute(_q("""
                CREATE TABLE IF NOT EXISTS app_state (
                    state_key TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erro ao inicializar app_state: {e}")

    @staticmethod
    def _pg_get(key: str) -> Optional[str]:
        conn = get_connection()
        c = conn.cursor()
        c.execute(_q("SELECT state_json FROM app_state WHERE state_key = ?"), (key,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None

    @staticmethod
    def _pg_set(key: str, raw: str):
        conn = get_connection()
        c = conn.cursor()
        c.execute(_q("""
            INSERT INTO app_state (state_key, state_json, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (state_key) DO UPDATE
            SET state_json = EXCLUDED.state_json, updated_at = CURRENT_TIMESTAMP
        """), (key, raw))
        conn.commit()
        conn.close()

    @staticmethod
    def load_from_disk() -> Dict[str, Any]:
        """Carrega estado do Postgres (se configurado) ou do disco - SEMPRE pega a versão mais recente"""
        with _file_lock:
            try:
                raw = SharedState._pg_get('shared_state') if _usar_postgres() else (
                    STATE_FILE.read_text() if STATE_FILE.exists() else None
                )

                if raw:
                    data = json.loads(raw)

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
        """Salva estado no Postgres (se configurado) ou no disco - TODAS as sessões compartilham este estado"""
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

                raw = json.dumps(save_data, default=str, ensure_ascii=False, indent=2)
                if _usar_postgres():
                    SharedState._pg_set('shared_state', raw)
                else:
                    STATE_FILE.write_text(raw)
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
        # PERFORMANCE: se ESTA sessão acabou de salvar (rerun disparado por um
        # clique seu), st.session_state já reflete exatamente o que foi salvo -
        # reler agora seria 1 round-trip redundante ao Postgres. Só pula essa
        # única vez; outras sessões/autorefresh continuam sincronizando normal.
        if st.session_state.pop('_shared_state_just_saved', False):
            return

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
        st.session_state['_shared_state_just_saved'] = True
    
    @staticmethod
    @st.cache_data(ttl=15)  # PERFORMANCE: evita reconsultar o Postgres a cada rerun (colaboradores_extras/demandas_publicas mudam raramente)
    def _fetch_admin_data_cached():
        raw = SharedState._pg_get('admin_data') if _usar_postgres() else (
            ADMIN_FILE.read_text() if ADMIN_FILE.exists() else None
        )
        return json.loads(raw) if raw else None

    @staticmethod
    def load_admin_data():
        """Carrega dados administrativos (cache de 15s para reduzir round-trips ao Postgres)"""
        with _file_lock:
            try:
                data = SharedState._fetch_admin_data_cached()
                if data:
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
                raw = json.dumps(data, default=str, ensure_ascii=False, indent=2)
                if _usar_postgres():
                    SharedState._pg_set('admin_data', raw)
                else:
                    ADMIN_FILE.write_text(raw)
                SharedState._fetch_admin_data_cached.clear()  # invalida o cache: a próxima leitura já vem atualizada
                return True
            except:
                return False


# Funções de conveniência para compatibilidade
def load_state():
    """Carrega estado compartilhado (compatibilidade)"""
    SharedState.sync_to_session_state()
    return True

def save_state():
    """Salva estado compartilhado (compatibilidade)"""
    SharedState.sync_from_session_state()

def load_admin_data():
    """Carrega dados admin (compatibilidade)"""
    return SharedState.load_admin_data()

def save_admin_data():
    """Salva dados admin (compatibilidade)"""
    return SharedState.save_admin_data()
