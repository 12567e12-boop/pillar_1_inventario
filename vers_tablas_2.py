import sqlite3
import os

databases = [
    r"c:\Users\dreat\OneDrive\Escritorio\DEMO\dreacht_hub_web-master\db.sqlite3",
    r"c:\Users\dreat\OneDrive\Escritorio\DEMO\pillar_1_inventario-main\db.sqlite3"
]

with open("tablas.txt", "w", encoding="utf-8") as f:
    for db_path in databases:
        f.write(f"\n--- Tablas en {os.path.basename(os.path.dirname(db_path))} ---\n")
        if not os.path.exists(db_path):
            f.write("DATABASE NOT FOUND\n")
            continue
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            tables.sort()
            for table in tables:
                f.write(f"{table}\n")
            conn.close()
        except Exception as e:
            f.write(f"Error: {e}\n")
