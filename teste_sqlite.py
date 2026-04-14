import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / "dados_libras.sqlite"
print("Criando banco em:", db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS teste (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT
)
""")

cursor.execute("INSERT INTO teste (nome) VALUES (?)", ("bom_dia",))
conn.commit()

cursor.execute("SELECT * FROM teste")
print(cursor.fetchall())

conn.close()