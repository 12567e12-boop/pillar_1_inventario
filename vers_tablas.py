import sqlite3
import os

databases = [
    r"c:\Users\dreat\OneDrive\Escritorio\DEMO\dreacht_hub_web-master\db.sqlite3",
    r"c:\Users\dreat\OneDrive\Escritorio\DEMO\pillar_1_inventario-main\db.sqlite3"
]

for db_path in databases:
    print(f"\n--- Tablas en {os.path.basename(os.path.dirname(db_path))} ---")
    if not os.path.exists(db_path):
        print("DATABASE NOT FOUND")
        continue
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        tables.sort()
        for table in tables:
            print(table)
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
