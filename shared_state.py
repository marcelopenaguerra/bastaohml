"""
Sistema de Estado Compartilhado
Persiste no Supabase (PostgreSQL) se configurado, senão usa arquivo local.
"""

import json
import streamlit as st
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import threading

# Arquivos locais (fallback)
STATE_FILE = Path("bastao_state.json")
ADMIN_FILE = Path("admin_data.json")

_file_lock = threading.Lock()

# ============================================================
# CAMADA DE PERSISTÊNCIA: PostgreSQL (Supabase) ou arquivo local
# ============================================================

def _usar_postgres():
    """Verifica se há PostgreSQL configurado nos secrets"""
    try:
        return (
            hasattr(st, 'secrets')
            and 'postgres' in st.secrets
            and bool(st.secrets['postgres'].get('url') or st.secrets['postgres'].get('host'))
        )
    except Exception:
        return False

def _get_pg_conn():
    """Retorna conexão psycopg2 ao Supabase"""
    import psycopg2
    pg = st.secrets['postgres']
    if pg.get('url'):
        return psycopg2.connect(pg['url'])
    return psycopg2.connect(
        host=pg['host'], port=pg.get('port', 5432),
        dbname=pg['dbname'], user=pg['user'],
        password=pg['password'], sslmode=pg.get('sslmode', 'require')
    )

def _ensure_state_table(conn):
    """Cria tabela bastao_state se não existir"""
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bastao_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

def _pg_load(key: str) -> Any:
    """Carrega valor do PostgreSQL"""
    try:
        conn = _get_pg_conn()
        _ensure_state_table(conn)
        c = conn.cursor()
        c.execute("SELECT value FROM bastao_state WHERE key = %s", (key,))
        row = c.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
    except Exception as e:
        print(f"ERRO _pg_load({key}): {e}")
    return None

def _pg_save(key: str, value: Any) -> bool:
    """Salva valor no PostgreSQL (upsert)"""
    try:
        conn = _get_pg_conn()
        _ensure_state_table(conn)
        c = conn.cursor()
        c.execute("""
            INSERT INTO bastao_state (key, value, updated_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (key) DO UPDATE
            SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP
        """, (key, json.dumps(value, default=str, ensure_ascii=False)))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"ERRO _pg_save({key}): {e}")
        return False

# ============================================================
# SERIALIZAÇÃO / DESERIALIZAÇÃO
# ============================================================

def _serialize(data: dict) -> dict:
    """Converte datetime → string ISO para JSON"""
    out = data.copy()
    if isinstance(out.get('bastao_start_time'), datetime):
        out['bastao_start_time'] = out['bastao_start_time'].isoformat()
    out['almoco_times'] = {
        k: v.isoformat() if isinstance(v, datetime) else v
        for k, v in out.get('almoco_times', {}).items()
    }
    out['demanda_start_times'] = {
        k: v.isoformat() if isinstance(v, datetime) else v
        for k, v in out.get('demanda_start_times', {}).items()
    }
    return out

def _deserialize(data: dict) -> dict:
    """Converte strings ISO → datetime"""
    if data.get('bastao_start_time'):
        try:
            data['bastao_start_time'] = datetime.fromisoformat(data['bastao_start_time'])
        except Exception:
            data['bastao_start_time'] = None
    data['almoco_times'] = {
        k: datetime.fromisoformat(v) if isinstance(v, str) else v
        for k, v in data.get('almoco_times', {}).items()
    }
    data['demanda_start_times'] = {
        k: datetime.fromisoformat(v) if isinstance(v, str) else v
        for k, v in data.get('demanda_start_times', {}).items()
    }
    return data

def _empty_state() -> dict:
    return {
        'bastao_queue': [], 'status_texto': {}, 'bastao_start_time': None,
        'bastao_counts': {}, 'simon_ranking': [], 'daily_logs': [],
        'checks': {}, 'almoco_times': {}, 'demanda_start_times': {}, 'demanda_logs': []
    }

# ============================================================
# SharedState
# ============================================================

class SharedState:

    @staticmethod
    def init_db():
        """Cria tabela bastao_state no PostgreSQL se não existir (chamado na inicialização)"""
        if _usar_postgres():
            try:
                conn = _get_pg_conn()
                _ensure_state_table(conn)
                conn.close()
                print("✅ SharedState: tabela bastao_state pronta no PostgreSQL")
            except Exception as e:
                print(f"ERRO SharedState.init_db: {e}")

    @staticmethod
    def load_from_disk() -> dict:
        if _usar_postgres():
            data = _pg_load('bastao_state')
            if data:
                return _deserialize(data)
            return _empty_state()
        # Fallback: arquivo local
        with _file_lock:
            try:
                if STATE_FILE.exists():
                    return _deserialize(json.loads(STATE_FILE.read_text()))
            except Exception as e:
                print(f"Erro ao carregar estado local: {e}")
        return _empty_state()

    @staticmethod
    def save_to_disk(data: dict):
        serialized = _serialize(data)
        if _usar_postgres():
            _pg_save('bastao_state', serialized)
            return
        # Fallback: arquivo local
        with _file_lock:
            try:
                STATE_FILE.write_text(json.dumps(serialized, default=str, ensure_ascii=False, indent=2))
            except Exception as e:
                print(f"Erro ao salvar estado local: {e}")

    @staticmethod
    def sync_to_session_state():
        """Carrega estado persistido → session_state"""
        disk_data = SharedState.load_from_disk()
        st.session_state.bastao_queue        = disk_data.get('bastao_queue', [])
        st.session_state.status_texto        = disk_data.get('status_texto', {})
        st.session_state.bastao_start_time   = disk_data.get('bastao_start_time')
        st.session_state.bastao_counts       = disk_data.get('bastao_counts', {})
        st.session_state.simon_ranking       = disk_data.get('simon_ranking', [])
        st.session_state.daily_logs          = disk_data.get('daily_logs', [])
        st.session_state.almoco_times        = disk_data.get('almoco_times', {})
        st.session_state.demanda_start_times = disk_data.get('demanda_start_times', {})
        st.session_state.demanda_logs        = disk_data.get('demanda_logs', [])
        for nome, val in disk_data.get('checks', {}).items():
            st.session_state[f'check_{nome}'] = val

    @staticmethod
    def sync_from_session_state():
        """Salva session_state → persistência"""
        checks = {
            k.replace('check_', ''): st.session_state[k]
            for k in st.session_state.keys() if k.startswith('check_')
        }
        data = {
            'bastao_queue':        st.session_state.get('bastao_queue', []),
            'status_texto':        st.session_state.get('status_texto', {}),
            'bastao_start_time':   st.session_state.get('bastao_start_time'),
            'bastao_counts':       st.session_state.get('bastao_counts', {}),
            'simon_ranking':       st.session_state.get('simon_ranking', []),
            'daily_logs':          st.session_state.get('daily_logs', []),
            'almoco_times':        st.session_state.get('almoco_times', {}),
            'demanda_start_times': st.session_state.get('demanda_start_times', {}),
            'demanda_logs':        st.session_state.get('demanda_logs', []),
            'checks':              checks,
        }
        SharedState.save_to_disk(data)

    @staticmethod
    def load_admin_data():
        if _usar_postgres():
            data = _pg_load('admin_data')
            if data:
                st.session_state.colaboradores_extras = data.get('colaboradores_extras', [])
                st.session_state.demandas_publicas    = data.get('demandas_publicas', [])
                return True
            return False
        with _file_lock:
            try:
                if ADMIN_FILE.exists():
                    data = json.loads(ADMIN_FILE.read_text())
                    st.session_state.colaboradores_extras = data.get('colaboradores_extras', [])
                    st.session_state.demandas_publicas    = data.get('demandas_publicas', [])
                    return True
            except Exception:
                pass
        return False

    @staticmethod
    def save_admin_data():
        data = {
            'colaboradores_extras': st.session_state.get('colaboradores_extras', []),
            'demandas_publicas':    st.session_state.get('demandas_publicas', []),
        }
        if _usar_postgres():
            _pg_save('admin_data', data)
            return True
        with _file_lock:
            try:
                ADMIN_FILE.write_text(json.dumps(data, default=str, ensure_ascii=False, indent=2))
                return True
            except Exception:
                return False


# Funções de conveniência (compatibilidade com código existente)
def load_state():
    SharedState.sync_to_session_state()
    return True

def save_state():
    SharedState.sync_from_session_state()

def load_admin_data():
    return SharedState.load_admin_data()

def save_admin_data():
    return SharedState.save_admin_data()
