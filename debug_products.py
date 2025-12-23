import sqlite3

db_path = r"c:\Users\dreat\OneDrive\Escritorio\DEMO\pillar_1_inventario-main\db.sqlite3"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    specialties = ['plomeria', 'PLOMERIA', 'Plomeria', 'Plomería', 'plomería']
    
    print("--- Searching for variations of 'plomeria' ---")
    for s in specialties:
        query = "SELECT id, nombre, especialidad FROM Almacen_producto WHERE especialidad LIKE ?"
        cursor.execute(query, [f"%{s}%"])
        rows = cursor.fetchall()
        print(f"Query '%{s}%': Found {len(rows)} rows")
        if rows:
            print(f"  Example: {rows[0]}")

    print("\n--- Listing ALL specialties in DB ---")
    cursor.execute("SELECT DISTINCT especialidad FROM Almacen_producto")
    print(cursor.fetchall())
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
