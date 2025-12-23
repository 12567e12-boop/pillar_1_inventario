# 🚀 GUÍA RÁPIDA - DREACHT HUB

## ⚡ Inicio Rápido (5 minutos)

### 1. Activar Entorno Virtual
```powershell
dreacht_venv\Scripts\activate
```

### 2. Ejecutar Servidor
```powershell
python manage.py runserver
```

### 3. Acceder a la Aplicación
```
http://localhost:8000
```

---

## 📍 Navegación

| URL | Función |
|-----|---------|
| `/` | Página de inicio |
| `/gafetes/` | Crear gafetes de empleados |
| `/requisiciones/` | Crear requisiciones y generar PDFs |
| `/recursos/` | Recursos (ejemplo) |
| `/admin/` | Panel de administración |

---

## 📋 Crear una Requisición (Paso a Paso)

1. **Ir a** → `http://localhost:8000/requisiciones/`
2. **Rellenar campos:**
   - Obra (obligatorio)
   - Ubicación (obligatorio)
   - Contratista Solicitante (obligatorio)
   - Contratista Autorizante (obligatorio)
   - Área de Utilidad (obligatorio)
   - Fechas (solicitud obligatoria, utilidad y surtimiento opcionales)
3. **Agregar items** (hasta 14):
   - Descripción
   - Unidad
   - Cantidad
4. **Click en** "Generar PDF"
5. **Descargar** el PDF automáticamente

---

## 🧪 Ejecutar Tests

```powershell
# Todos los tests
python manage.py test app_PDF_maker

# Test específico
python manage.py test app_PDF_maker.RequisicionFormTests.test_valid_form
```

---

## 📊 Ver Logs

```powershell
# Logs de la app
Get-Content logs\app_PDF_maker.log -Tail 20

# Logs de Django
Get-Content logs\django.log -Tail 20

# Monitorear en tiempo real
Get-Content -Path logs\app_PDF_maker.log -Wait
```

---

## 🔧 Crear Empleado (Admin)

```powershell
# Entrar al admin
python manage.py createsuperuser  # (si no existe)
# Ir a http://localhost:8000/admin/
```

---

## 📦 Reinstalar Dependencias

```powershell
pip install -r requirements.txt
```

---

## ❌ Solucionar Problemas

### Error: "plantilla base no encontrada"
```
✓ Verificar que media/requiscion_template.pdf existe
✓ Crear el archivo si falta
```

### Error: "No module named 'app_PDF_maker'"
```powershell
# Reinstalar dependencias
pip install -r requirements.txt

# Ir a directorio raíz del proyecto
cd dreacht_hub_web-master
```

### Error: "Permission denied"
```powershell
# Cambiar permisos (Windows)
icacls "logs" /grant "Everyone":F
```

---

## 🔐 Antes de Producción

```python
# 1. En settings.py cambiar:
DEBUG = False
ALLOWED_HOSTS = ['tu-dominio.com']

# 2. Cambiar SECRET_KEY (generar nueva)
# Usar: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# 3. Crear superuser
python manage.py createsuperuser

# 4. Recolectar archivos estáticos
python manage.py collectstatic
```

---

## 📁 Estructura Importante

```
dreacht_hub_web-master/
├── logs/                          # Archivos de log
├── media/                         # Uploads (gafetes, PDFs)
├── app_PDF_maker/                # App principal
│   ├── forms.py                  # Formularios
│   ├── models.py                 # Modelos
│   ├── views/                    # Vistas
│   ├── templates/                # Templates HTML
│   └── tests.py                  # Tests unitarios
├── empleados/                    # App de empleados
│   └── models.py                 # Modelos (Requisicion, DetalleRequisicion, etc.)
├── dreacht_hub/                  # Configuración
│   └── settings.py               # Configuración del proyecto
├── manage.py                     # CLI de Django
└── requirements.txt              # Dependencias
```

---

## 📚 Archivos de Documentación

- `MEJORAS.md` - Cambios realizados
- `TODO_ACTUALIZADO.md` - Estado del proyecto
- `RESUMEN_CORRECCIONES.md` - Resumen detallado
- `CHECKLIST_FINAL.md` - Checklist completo

---

## 💡 Tips

1. **Usar Django Shell** para debuggear:
```powershell
python manage.py shell
>>> from empleados.models import Requisicion
>>> Requisicion.objects.all()
```

2. **Limpiar BD** (⚠️ borra todo):
```powershell
python manage.py flush
```

3. **Hacer migraciones** si cambias modelos:
```powershell
python manage.py makemigrations
python manage.py migrate
```

---

**¡Proyecto listo para usar! 🎉**

Para más ayuda, revisa los archivos de documentación incluidos.
