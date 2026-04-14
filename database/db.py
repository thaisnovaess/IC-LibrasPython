import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "dados_libras.sqlite"

def conectar():
    print("Banco em uso:", DB_PATH)
    return sqlite3.connect(DB_PATH)

def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sinais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_sinal TEXT NOT NULL,
        observacao TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hand_landmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sinal_id INTEGER NOT NULL,
        frame_num INTEGER NOT NULL,
        hand_id INTEGER NOT NULL,
        landmark_id INTEGER NOT NULL,
        x REAL NOT NULL,
        y REAL NOT NULL,
        z REAL NOT NULL,
        FOREIGN KEY (sinal_id) REFERENCES sinais(id)
    )
    """)

    conn.commit()
    conn.close()

def inserir_sinal(nome_sinal, observacao=None):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO sinais (nome_sinal, observacao)
    VALUES (?, ?)
    """, (nome_sinal, observacao))

    sinal_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return sinal_id

def inserir_landmark(sinal_id, frame_num, hand_id, landmark_id, x, y, z):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO hand_landmarks (sinal_id, frame_num, hand_id, landmark_id, x, y, z)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (sinal_id, frame_num, hand_id, landmark_id, x, y, z))

    conn.commit()
    conn.close()