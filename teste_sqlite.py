"""Demonstração manual e isolada de acesso ao SQLite."""

import sqlite3
from contextlib import closing
from pathlib import Path


def main() -> None:
    db_path = Path(__file__).resolve().parent / "dados_libras.sqlite"
    print("Criando banco em:", db_path)

    with closing(sqlite3.connect(db_path)) as connection:
        with connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS teste (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT
                )
                """
            )
            cursor.execute("INSERT INTO teste (nome) VALUES (?)", ("bom_dia",))
            cursor.execute("SELECT * FROM teste")
            print(cursor.fetchall())


if __name__ == "__main__":
    main()
