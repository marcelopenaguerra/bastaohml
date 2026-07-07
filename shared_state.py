"""
Sistema de Estado Compartilhado
Persiste no Supabase (PostgreSQL) se configurado, senão usa arquivo local.
"""

import json
import streamlit as st
from pathlib import Path
from datetime import datetime
from typing import Any
import threading

STATE_FILE = Path("bastao_state.json")
ADMIN_FILE  = Path("admin_data.json")
_file_lock  = threading.Lock()
_table_ensured = False


# ── helpers PostgreSQL ────────────────────────────────────────────────────────

def _usar_postgres():
    try:
        return (
            hasattr(st, "secrets")
            and "postgres" in st.secrets
            and bool(st.secrets["postgres"].get("url") or st.secrets["postgres"].get("host"))
        )
    except Exception:
        return False

def _get_pg_conn():
    import psycopg2
    pg = st.secrets["postgres"]
    if pg.get("url"):
        return psycopg2.connect(pg["url"])
    return psycopg2.connect(
        host=pg["host"], port=pg.get("port", 5432),
        dbname=pg["dbname"], user=pg["user"],
        password=pg["password"], sslmode=pg.get("sslmode", "require"),
    )

def _ensure_table(conn):
    global _table_ensured
    if _table_ensured:
        return
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bastao_state (
            key        TEXT PRIMARY KEY,
            value      TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    _table_ensured = True

def _pg_load_all():
    """Carrega bastao_state E admin_data em UMA única conexão."""
    try:
        conn = _get_pg_conn()
        _ensure_table(conn)
        c = conn.cursor()
        c.execute("SELECT key, value FROM bastao_state WHERE key IN ('bastao_state','admin_data')")
        rows = {r[0]: json.loads(r[1]) for r in c.fetchall()}
        conn.close()
        return rows.get("bastao_state"), rows.get("admin_data")
    except Exception as e:
        print(f"ERRO _pg_load_all: {e}")
        return None, None

def _pg_save(key: str, value: Any, conn=None):
    """Salva um valor. Reusa conn se fornecida."""
    close_after = conn is None
    try:
        if conn is None:
            conn = _get_pg_conn()
            _ensure_table(conn)
        c = conn.cursor()
        c.execute("""
            INSERT INTO bastao_state (key, value, updated_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (key) DO UPDATE
            SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP
        """, (key, json.dumps(value, default=str, ensure_ascii=False)))
        conn.commit()
        if close_after:
            conn.close()
        return True
    except Exception as e:
        print(f"ERRO _pg_save({key}): {e}")
        return False


# ── serialização ─────────────────────────────────────────────────────────────

def _serialize(data: dict) -> dict:
    out = data.copy()
    if isinstance(out.get("bastao_start_time"), datetime):
        out["bastao_start_time"] = out["bastao_start_time"].isoformat()
    out["almoco_times"]        = {k: v.isoformat() if isinstance(v, datetime) else v for k, v in out.get("almoco_times", {}).items()}
    out["demanda_start_times"] = {k: v.isoformat() if isinstance(v, datetime) else v for k, v in out.get("demanda_start_times", {}).items()}
    return out

def _deserialize(data: dict) -> dict:
    if data.get("bastao_start_time"):
        try:   data["bastao_start_time"] = datetime.fromisoformat(data["bastao_start_time"])
        except: data["bastao_start_time"] = None
    data["almoco_times"]        = {k: datetime.fromisoformat(v) if isinstance(v, str) else v for k, v in data.get("almoco_times", {}).items()}
    data["demanda_start_times"] = {k: datetime.fromisoformat(v) if isinstance(v, str) else v for k, v in data.get("demanda_start_times", {}).items()}
    return data

def _empty_state() -> dict:
    return {
        "bastao_queue": [], "status_texto": {}, "bastao_start_time": None,
        "bastao_counts": {}, "simon_ranking": [], "daily_logs": [],
        "checks": {}, "almoco_times": {}, "demanda_start_times": {}, "demanda_logs": [],
    }


# ── SharedState ───────────────────────────────────────────────────────────────

class SharedState:

    @staticmethod
    def init_db():
        if _usar_postgres():
            try:
                conn = _get_pg_conn()
                _ensure_table(conn)
                conn.close()
                print("✅ SharedState: tabela bastao_state pronta no PostgreSQL")
            except Exception as e:
                print(f"ERRO SharedState.init_db: {e}")

    @staticmethod
    def sync_all():
        """
        Carrega bastao_state + admin_data em UMA conexão PostgreSQL.
        Substitui as duas chamadas separadas (sync_to_session_state + load_admin_data).
        """
        if _usar_postgres():
            state_data, admin_data = _pg_load_all()
        else:
            state_data = admin_data = None
            with _file_lock:
                try:
                    if STATE_FILE.exists():
                        state_data = json.loads(STATE_FILE.read_text())
                except Exception as e:
                    print(f"Erro carregar state local: {e}")
                try:
                    if ADMIN_FILE.exists():
                        admin_data = json.loads(ADMIN_FILE.read_text())
                except Exception as e:
                    print(f"Erro carregar admin local: {e}")

        # ── aplicar state ──
        s = _deserialize(state_data) if state_data else _empty_state()
        st.session_state.bastao_queue        = s.get("bastao_queue", [])
        st.session_state.status_texto        = s.get("status_texto", {})
        st.session_state.bastao_start_time   = s.get("bastao_start_time")
        st.session_state.bastao_counts       = s.get("bastao_counts", {})
        st.session_state.simon_ranking       = s.get("simon_ranking", [])
        st.session_state.daily_logs          = s.get("daily_logs", [])
        st.session_state.almoco_times        = s.get("almoco_times", {})
        st.session_state.demanda_start_times = s.get("demanda_start_times", {})
        st.session_state.demanda_logs        = s.get("demanda_logs", [])
        for nome, val in s.get("checks", {}).items():
            st.session_state[f"check_{nome}"] = val

        # ── aplicar admin ──
        if admin_data:
            st.session_state.colaboradores_extras = admin_data.get("colaboradores_extras", [])
            st.session_state.demandas_publicas    = admin_data.get("demandas_publicas", [])

    @staticmethod
    def sync_to_session_state():
        """Mantido por compatibilidade — usa sync_all internamente."""
        SharedState.sync_all()

    @staticmethod
    def sync_from_session_state():
        """Salva estado da sessão → banco."""
        checks = {
            k.replace("check_", ""): st.session_state[k]
            for k in st.session_state if k.startswith("check_")
        }
        state_data = _serialize({
            "bastao_queue":        st.session_state.get("bastao_queue", []),
            "status_texto":        st.session_state.get("status_texto", {}),
            "bastao_start_time":   st.session_state.get("bastao_start_time"),
            "bastao_counts":       st.session_state.get("bastao_counts", {}),
            "simon_ranking":       st.session_state.get("simon_ranking", []),
            "daily_logs":          st.session_state.get("daily_logs", []),
            "almoco_times":        st.session_state.get("almoco_times", {}),
            "demanda_start_times": st.session_state.get("demanda_start_times", {}),
            "demanda_logs":        st.session_state.get("demanda_logs", []),
            "checks":              checks,
        })
        if _usar_postgres():
            try:
                conn = _get_pg_conn()
                _ensure_table(conn)
                _pg_save("bastao_state", state_data, conn)
                conn.close()
            except Exception as e:
                print(f"ERRO sync_from_session_state: {e}")
        else:
            with _file_lock:
                try:
                    STATE_FILE.write_text(json.dumps(state_data, default=str, ensure_ascii=False, indent=2))
                except Exception as e:
                    print(f"Erro salvar state local: {e}")

    @staticmethod
    def load_admin_data():
        """Mantido por compatibilidade — usa sync_all internamente."""
        SharedState.sync_all()
        return True

    @staticmethod
    def save_admin_data():
        admin_data = {
            "colaboradores_extras": st.session_state.get("colaboradores_extras", []),
            "demandas_publicas":    st.session_state.get("demandas_publicas", []),
        }
        if _usar_postgres():
            return _pg_save("admin_data", admin_data)
        with _file_lock:
            try:
                ADMIN_FILE.write_text(json.dumps(admin_data, default=str, ensure_ascii=False, indent=2))
                return True
            except Exception:
                return False


# ── funções de conveniência ───────────────────────────────────────────────────

def load_state():
    SharedState.sync_all()
    return True

def save_state():
    SharedState.sync_from_session_state()

def load_admin_data():
    return SharedState.load_admin_data()

def save_admin_data():
    return SharedState.save_admin_data()
