# 📸 Manejo de Imágenes en Requisiciones

## 📋 Visión General

El sistema de gestión de inventario incluye un flujo completo para adjuntar imágenes a las requisiciones. Este documento detalla cómo funciona el proceso y cómo solucionar problemas comunes.

## 🔍 Flujo de Carga de Imágenes

1. **Creación de Requisición**
   - El usuario selecciona "Nueva Requisición"
   - Completa los detalles (obra, ubicación, etc.)
   - El sistema solicita una imagen obligatoria

2. **Procesamiento**
   - La imagen se guarda en `media/requisiciones/`
   - Se asocia con la requisición en la base de datos
   - Se genera una vista previa en el listado

3. **Visualización**
   - Los usuarios pueden ver la imagen de cualquier requisición
   - Los supervisores pueden aprobar/rechazar basados en la imagen

## 🛠️ Configuración Requerida

### Dependencias
Asegúrate de tener instalados estos paquetes:

```bash
pip install Pillow==10.1.0  # Para procesamiento de imágenes
pip install python-telegram-bot==20.7  # Para manejo de archivos en Telegram
```

### Configuración de Django
En `settings.py` verifica:

```python
# Configuración de archivos estáticos y multimedia
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Asegúrate de que exista el directorio para las imágenes
os.makedirs(os.path.join(MEDIA_ROOT, 'requisiciones'), exist_ok=True)
```

```cmd
cd c:\Users\dreat\OneDrive\Escritorio\dead_or_alive\Dreacht_hub_inventario-master\Dreacht_hub_inventario-master
laZona\Scripts\activate
pip install Pillow asgiref
```

O simplemente ejecuta:
```cmd
instalar_dependencias.bat
```

### 2. Verificar instalación

Ejecuta este comando para verificar que todo está instalado:

```cmd
python test_dependencias.py
```

Deberías ver:
```
✓ Django                        - INSTALADO
✓ python-telegram-bot           - INSTALADO
✓ Pillow                        - INSTALADO
✓ asgiref                       - INSTALADO
```

### 3. Reiniciar el bot

**Detén el bot** (Ctrl+C) y vuelve a iniciarlo:

```cmd
python manage.py run_telegram_bot
```

O usa:
```cmd
iniciar_bot.bat
```

### 4. Probar en Telegram

1. Abre Telegram y busca tu bot
2. Envía `/nueva`
3. Completa todos los pasos hasta llegar a la imagen
## 🚀 Uso del Sistema de Imágenes

### Para Usuarios:
1. Inicia una nueva requisición con `/nueva`
2. Completa los datos solicitados
3. **Obligatorio**: Adjunta una imagen cuando se te solicite
   - Puedes tomar una foto o subir una existente
   - Asegúrate de que la imagen sea clara y legible
4. Espera la confirmación del sistema

### Para Supervisores:
1. Usa `/ver <ID>` para ver una requisición
2. Haz clic en "👁️ Ver Imagen" para ver la imagen adjunta
3. Aprueba o rechaza según corresponda

## 🔍 Solución de Problemas Comunes

### Error: "No se pudo guardar la imagen"
**Posibles causas:**
- Permisos de escritura en la carpeta `media/requisiciones/`
- Espacio en disco insuficiente
- Problemas con el formato de la imagen

**Soluciones:**
1. Verifica los permisos de la carpeta:
   ```bash
   chmod -R 755 media/
   chown -R www-data:www-data media/  # Ajusta el usuario según tu configuración
   ```

2. Verifica el espacio en disco:
   ```bash
   df -h
   ```

3. Intenta con una imagen diferente o en otro formato (JPEG/PNG)

### Error: "No se encontró la imagen"
**Causa:** La imagen se eliminó o movió manualmente

**Solución:**
1. Verifica que el archivo exista en `media/requisiciones/`
2. Si la imagen se perdió, solicita al usuario que la envíe de nuevo
3. Actualiza la ruta en la base de datos si es necesario

## 🛠️ Mantenimiento

### Limpieza de Imágenes
Para eliminar imágenes no utilizadas:
```python
from django.db.models import Q
from Almacen.models.requisiciones.requisiciones import Requisicion
import os

# Encontrar imágenes huérfanas (que no están asociadas a ninguna requisición)
used_images = set(Requisicion.objects.exclude(imagen='').values_list('imagen', flat=True))
media_path = 'media/requisiciones/'

for filename in os.listdir(media_path):
    if filename not in used_images and filename != 'default.jpg':
        os.remove(os.path.join(media_path, filename))
        print(f"Eliminada: {filename}")
```

### Respaldo
Asegúrate de incluir la carpeta `media/` en tus copias de seguridad.

## 📈 Métricas
- Tamaño máximo por imagen: 10MB
- Formatos soportados: JPEG, PNG
- Ruta de almacenamiento: `media/requisiciones/`
- Nombre de archivo: `requisicion_<UUID>.jpg`

## 📞 Soporte
Si encuentras algún problema:
1. Revisa los logs del servidor
2. Verifica los permisos de archivos
3. Contacta al equipo de soporte con:
   - Captura del error
   - ID de la requisición
   - Hora exacta del error
