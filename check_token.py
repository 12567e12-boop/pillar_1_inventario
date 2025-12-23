import sqlite3

# Conectar a la base de datos de Inventario
conn = sqlite3.connect('pillar_1_inventario-main/db.sqlite3')
cursor = conn.cursor()

# Buscar la requisición
cursor.execute('''
    SELECT id, token_publico, obra, ubicacion, especialidad 
    FROM Almacen_requisicion 
    WHERE id = "UMA-UMA-0003-PLO"
''')

result = cursor.fetchone()
if result:
    print(f"\n✅ Requisición encontrada:")
    print(f"  ID: {result[0]}")
    print(f"  Token: {result[1]}")
    print(f"  Obra: {result[2]}")
    print(f"  Ubicación: {result[3]}")
    print(f"  Especialidad: {result[4]}")
else:
    print("\n❌ Requisición NO encontrada")

# Buscar por token
token = "7accde56-de10-48cb-a6a2-4ce07ff9e22d"
cursor.execute('''
    SELECT id, token_publico, obra 
    FROM Almacen_requisicion 
    WHERE token_publico = ?
''', [token])

result2 = cursor.fetchone()
if result2:
    print(f"\n✅ Búsqueda por token exitosa:")
    print(f"  ID: {result2[0]}")
    print(f"  Token: {result2[1]}")
else:
    print(f"\n❌ NO se encontró requisición con token: {token}")

conn.close()
