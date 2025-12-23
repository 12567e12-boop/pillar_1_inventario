# TODO: Implementar Validación de Formularios en Requisiciones

## Información Recopilada
- El formulario actual en `requisiciones.html` es HTML puro sin validaciones Django.
- La vista `views_requisicion.py` procesa datos manualmente con `request.POST`.
- Modelo `Requisicion` en `empleados/models.py` define los campos.
- `forms.py` tiene `EmpleadoForm`, pero falta `RequisicionForm`.
- Campos principales a validar: obra, ubicacion, numero_de_articulos, fecha_soli, fecha_util, fecha_surt, contratista_soli, contratista_auto, area_util, observaciones.
- Items (14 filas) son dinámicos; validar manualmente por ahora.

## Plan
1. Crear `RequisicionForm` en `app_PDF_maker/forms.py` con validaciones:
   - Campos requeridos: obra, ubicacion, fecha_soli, contratista_soli, contratista_auto, area_util.
   - numero_de_articulos: entero positivo.
   - Fechas: validar orden (fecha_soli <= fecha_util <= fecha_surt).
   - Longitudes: según modelo (e.g., obra max 200).
2. Modificar `app_PDF_maker/views/views_requisicion.py`:
   - Usar `RequisicionForm` en GET y POST.
   - Validar en POST; si inválido, render con errores.
3. Actualizar `app_PDF_maker/templates/app_PDF_maker/requisiciones.html`:
   - Cambiar inputs a `{{ form.obra }}`, etc., manteniendo attrs para posiciones absolutas.
   - Agregar manejo de errores: `{{ form.errors }}` o por campo.
4. Validar items manualmente en vista (descripción requerida si presente, cantidad numérica).

## Archivos Dependientes
- `app_PDF_maker/forms.py`: Agregar RequisicionForm.
- `app_PDF_maker/views/views_requisicion.py`: Modificar para usar form.
- `app_PDF_maker/templates/app_PDF_maker/requisiciones.html`: Actualizar template.
- `empleados/models.py`: Referencia para campos.

## Pasos de Seguimiento
- [x] Implementar RequisicionForm.
- [x] Modificar vista.
- [x] Actualizar template.
- [x] Probar validaciones: campos vacíos, tipos incorrectos, fechas inválidas.
- [x] Verificar generación de PDF solo si válido.
