from django.http import JsonResponse
from django.db import connections
import logging

logger = logging.getLogger(__name__)

def get_productos_por_especialidad(request):
    especialidad = request.GET.get('especialidad', '').strip()
    
    if not especialidad:
        return JsonResponse({'productos': []})

    productos = []
    try:
        # Query 'pilar' database (Inventory)
        # Table: Almacen_producto
        # Columns: nombre, unidad
        # Filter: especialidad (ILIKE or similar depending on DB, sqlite uses LIKE usually case-insensitive for ASCII)
        
        with connections['pilar'].cursor() as cursor:
            # Seleccionar id, nombre y el nombre de la unidad (JOIN)
            # Corregido: unidad_id es la FK, unidad es la tabla
            logger.info(f"Searching products with specialty matching: {especialidad}")
            
            # Use raw SQL join to get unit name
            query = """
                SELECT p.id, p.nombre, u.nombre 
                FROM Almacen_producto p
                LEFT JOIN Almacen_unidad u ON p.unidad_id = u.id
                WHERE p.especialidad LIKE %s 
                ORDER BY p.nombre ASC
            """
            cursor.execute(query, [f"%{especialidad}%"])
            rows = cursor.fetchall()
            
            logger.info(f"Found {len(rows)} products")

            for row in rows:
                productos.append({
                    'id': row[0],
                    'nombre': row[1],
                    'unidad': row[2] if row[2] else 'N/A' # Handle nulls if any
                })

    except Exception as e:
        logger.error(f"Error fetching products from pilar DB: {e}")
        return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'productos': productos})
