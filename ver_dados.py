import sqlite3

conn = sqlite3.connect("dados_libras.sqlite")
cursor = conn.cursor()

print("Tabela sinais:")
cursor.execute("SELECT * FROM sinais")
print(cursor.fetchall())

print("\nAlguns landmarks:")
cursor.execute("SELECT * FROM hand_landmarks LIMIT 10")
print(cursor.fetchall())

conn.close()