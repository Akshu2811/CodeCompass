import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS ingest_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_url TEXT UNIQUE,
            status TEXT
        );
        CREATE TABLE IF NOT EXISTS modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_url TEXT,
            path TEXT,
            content TEXT,
            summary TEXT,
            vector_blob BLOB,
            UNIQUE(repo_url, path)
        );
        CREATE TABLE IF NOT EXISTS qa_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_url TEXT,
            question TEXT,
            answer TEXT
        );
        CREATE TABLE IF NOT EXISTS onboarding_paths (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_url TEXT,
            guide_text TEXT,
            UNIQUE(repo_url)
        );
    ''')
    conn.commit()
    conn.close()

def set_job_status(repo_url, status):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO ingest_jobs (repo_url, status) VALUES (?, ?)", (repo_url, status))
    conn.commit()
    conn.close()

def get_job_status(repo_url):
    conn = get_connection()
    row = conn.execute("SELECT status FROM ingest_jobs WHERE repo_url = ?", (repo_url,)).fetchone()
    conn.close()
    return row['status'] if row else "not_found"

def save_module(repo_url, path, content, summary, vector_blob):
    conn = get_connection()
    conn.execute('''
        INSERT OR REPLACE INTO modules (repo_url, path, content, summary, vector_blob)
        VALUES (?, ?, ?, ?, ?)
    ''', (repo_url, path, content, summary, vector_blob))
    conn.commit()
    conn.close()

def get_all_modules(repo_url):
    conn = get_connection()
    rows = conn.execute("SELECT path, summary, vector_blob FROM modules WHERE repo_url = ?", (repo_url,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]
