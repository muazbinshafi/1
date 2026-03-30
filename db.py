import sqlite3
from contextlib import contextmanager

DATABASE_PATH = 'leads.db'

@contextmanager
def get_db(db_path=DATABASE_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db(db_path=DATABASE_PATH):
    with get_db(db_path) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL,
                contacted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

if __name__ == '__main__':
    init_db()
