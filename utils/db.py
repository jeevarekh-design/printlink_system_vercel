import os
import sqlite3

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None


def _is_postgres_conn(conn):
    return psycopg2 is not None and isinstance(conn, psycopg2.extensions.connection)


def get_db_connection():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if psycopg2 is None:
            raise RuntimeError("psycopg2 is required for PostgreSQL connections")

        # Vercel may provide postgres:// which psycopg2 supports if string conversion.
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        conn = psycopg2.connect(database_url, sslmode="require")
        return conn

    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "..", "database.db"))
    conn.row_factory = sqlite3.Row
    return conn


def execute_query(conn, query, params=None):
    params = params or []
    if _is_postgres_conn(conn):
        query = query.replace("?", "%s")
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        cur = conn.cursor()
    cur.execute(query, params)
    return cur
