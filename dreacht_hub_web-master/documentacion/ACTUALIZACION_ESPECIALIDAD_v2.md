# 🔄 ACTUALIZACIÓN: Especialidad como Dropdown Obligatorio

**Fecha:** 5 de Diciembre de 2024  
**Versión:** 1.2

---

## 📝 Cambios Realizados

Se cambió el campo **"especialidad"** de un campo de texto opcional a un **dropdown obligatorio** con 8 opciones predefinidas.

### Archivos Modificados:

1. **`app_PDF_maker/forms.py`**
   - Cambio: CharField → ChoiceField (Select widget)
   - Requerido: Ahora es obligatorio (required=True)
   - Opciones:
     - Plomería
     - Electricidad
     - Obra Civil
     - Vidrio y Cancelería
     - Pintura y Tablaroca
     - Herrería
     - Herramienta
     - Limpieza

2. **`empleados/models.py`**
   - Cambio: `blank=True` → `blank=False, default=''`
   - Cambio: `max_length=200` → `max_length=50`
   - Ahora es obligatorio en la BD

3. **`empleados/migrations/0007_requisicion_especialidad.py`**
   - Actualizada con nuevas configuraciones

4. **`app_PDF_maker/tests.py`**
   - Actualizado test_valid_form() con especialidad
   - Nuevo test: test_especialidad_required()

---

## 🎯 Valores Disponibles

```python
ESPECIALIDAD_CHOICES = [
    ('plomeria', 'Plomería'),
    ('electricidad', 'Electricidad'),
    ('obra civil', 'Obra Civil'),
    ('vidrio y canceleria', 'Vidrio y Cancelería'),
    ('pintura y tablaroca', 'Pintura y Tablaroca'),
    ('herreria', 'Herrería'),
    ('herramienta', 'Herramienta'),
    ('limpieza', 'Limpieza'),
]
```

---

## 🚀 Próximos Pasos

### 1. Aplicar la Migración
```bash
python manage.py migrate
```

### 2. El Dropdown en el Formulario
El campo aparecerá como un dropdown (select) en el formulario web, ubicado después del campo "Área de Utilidad".

### 3. Validar
```bash
python manage.py test app_PDF_maker.RequisicionFormTests.test_especialidad_required
```

---

## 📊 Especificaciones del Campo

| Propiedad | Valor |
|-----------|-------|
| **Nombre** | especialidad |
| **Tipo de Dato** | CharField con opciones |
| **Máximo de Caracteres** | 50 |
| **Requerido** | Sí ✅ (required=True) |
| **Widget** | Select (Dropdown) |
| **En PDF** | Sí (coordenadas: 420, 505) |
| **Valores Válidos** | 8 opciones predefinidas |

---

## ✅ Validaciones

- ✅ Sin errores de sintaxis
- ✅ Migración actualizada
- ✅ Tests actualizados
- ✅ Campo es obligatorio
- ✅ Valores predefinidos

---

## 🧪 Tests Incluidos

1. **test_valid_form()** - Valida con especialidad
2. **test_especialidad_required()** - Verifica que sea obligatorio
3. **test_fecha_validation()** - Incluye especialidad

---

**Status:** ✅ Completado  
**Versión:** 1.2
