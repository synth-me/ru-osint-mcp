import sqlite3
import secrets
import hashlib
import os 
import sys 

os.chdir(os.path.dirname(os.path.abspath(__file__)))

DB_NAME = "tokens.sqlite"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_hash TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL
            )
        """)

def generate_token(user_name: str):

    raw_token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO tokens (token_hash, name) VALUES (?, ?)", (token_hash, user_name))
    
    print(f"Token generated for: {user_name}")
    print(f"SAVE THIS TOKEN: {raw_token}") 

if __name__ == "__main__":
    init_db()
    
    if len(sys.argv) >= 2 : 
        user = sys.argv[1]
        generate_token(user)
    else:
        print("Provide a user name")

# eof 