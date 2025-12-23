# Sistema de Surtido Parcial de Requisiciones

**Estado:** Funcionalidad Futura (Pendiente de Implementación)  
**Fecha de Documentación:** 22 de diciembre de 2025  
**Prioridad:** Media  
**Estimación de Desarrollo:** 1-3 días completos

---

## Descripción General

Implementar un sistema que permita registrar el surtido progresivo/parcial de requisiciones, donde cada producto puede entregarse en múltiples entregas hasta completar la cantidad solicitada.

## Objetivo

Permitir que las requisiciones se vayan completando por porcentajes, registrando entregas parciales de productos en diferentes momentos, proporcionando visibilidad clara del progreso de cada requisición.

---

## Casos de Uso

### Caso 1: Surtido Parcial
- Se solicitan 100 unidades de un producto
- Primera entrega: 30 unidades (30% completado)
- Segunda entrega: 50 unidades (80% completado)
- Tercera entrega: 20 unidades (100% completado)

### Caso 2: Productos con Diferentes Avances
- Producto A: 100% surtido
- Producto B: 50% surtido
- Producto C: 0% surtido (pendiente)
- **Progreso total de requisición:** 50%

### Caso 3: Surtido Incompleto
- Se solicitan 100 unidades
- Solo se pueden surtir 80 unidades (producto descontinuado)
- Se marca como "Parcialmente completado" con justificación

---

## Alcance Técnico

### 🔧 Backend - Inventario (Django)

#### Modificaciones al Modelo `Requisicion_detalle`

```python
# Campos adicionales necesarios
class Requisicion_detalle(models.Model):
    # ... campos existentes ...
    
    # Nuevos campos
    cantidad_solicitada = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad_surtida = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    porcentaje_completado = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Estado del surtido
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En Proceso'),
        ('COMPLETADO', 'Completado'),
        ('PARCIAL_FINAL', 'Parcialmente Completado (Final)'),
    ]
    estado_surtido = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    
    # Metadatos
    fecha_ultimo_surtido = models.DateTimeField(null=True, blank=True)
    observaciones_surtido = models.TextField(blank=True)
    
    def actualizar_porcentaje(self):
        if self.cantidad_solicitada > 0:
            self.porcentaje_completado = (self.cantidad_surtida / self.cantidad_solicitada) * 100
        self.save()
```

#### Tabla de Historial de Surtidos (Nueva)

```python
class HistorialSurtido(models.Model):
    """Registra cada entrega parcial de un producto"""
    
    requisicion_detalle = models.ForeignKey(Requisicion_detalle, on_delete=models.CASCADE, related_name='surtidos')
    cantidad_entregada = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_entrega = models.DateTimeField(auto_now_add=True)
    usuario_entrega = models.CharField(max_length=100)
    
    # Documentación
    observaciones = models.TextField(blank=True)
    documento_soporte = models.FileField(upload_to='surtidos/', null=True, blank=True)
    
    class Meta:
        ordering = ['-fecha_entrega']
```

#### Endpoints API Necesarios

```python
# GET /api/requisiciones/{id}/progreso/
# Obtener progreso completo de una requisición

# POST /api/requisicion-detalle/{id}/registrar-surtido/
# Registrar una entrega parcial
{
    "cantidad_entregada": 30,
    "observaciones": "Primera entrega del almacén central",
    "usuario_entrega": "admin"
}

# GET /api/requisicion-detalle/{id}/historial-surtido/
# Obtener historial completo de entregas de un producto

# PATCH /api/requisicion-detalle/{id}/marcar-final/
# Marcar como parcialmente completado (no se surtirá más)
```

---

### 🎨 Frontend - Dreacht Hub

#### Módulo de Surtido (Nueva Vista)

**Ubicación sugerida:** `/surtir-requisiciones/`

**Características:**
- Lista de requisiciones con filtros:
  - Todas / Pendientes / En Proceso / Completadas
  - Por especialidad
  - Por rango de fechas
  - Por porcentaje de avance

- Visualización de progreso:
  - Barra de progreso general de requisición
  - Tabla con productos y porcentaje individual
  - Indicadores visuales (colores, iconos)

- Formulario de registro de surtido:
  - Seleccionar producto de la requisición
  - Ingresar cantidad entregada
  - Validación: no exceder cantidad pendiente
  - Campo de observaciones
  - Botón "Marcar como final" si no se puede completar

#### Dashboard de Seguimiento

**Métricas a mostrar:**
- Total de requisiciones activas
- Porcentaje de completado promedio
- Requisiciones pendientes de surtido
- Productos más solicitados vs más surtidos
- Gráficas de tendencias

#### Mejoras en Vista de Requisiciones

- Agregar columna de "Progreso" con barra visual
- Badge de estado (Pendiente/En Proceso/Completado)
- Botón para acceder al módulo de surtido

---

### 🔄 Lógica de Negocio

#### Reglas de Validación

1. **No sobre-surtir:**
   ```python
   if (cantidad_surtida + cantidad_nueva) > cantidad_solicitada:
       raise ValidationError("No se puede surtir más de lo solicitado")
   ```

2. **Actualización automática de estados:**
   - `cantidad_surtida == 0` → PENDIENTE
   - `0 < cantidad_surtida < cantidad_solicitada` → EN_PROCESO
   - `cantidad_surtida == cantidad_solicitada` → COMPLETADO

3. **Cálculo de porcentaje de requisición:**
   ```python
   def calcular_progreso_requisicion(requisicion_id):
       detalles = Requisicion_detalle.objects.filter(requisicion_id=requisicion_id)
       total_solicitado = sum(d.cantidad_solicitada for d in detalles)
       total_surtido = sum(d.cantidad_surtida for d in detalles)
       return (total_surtido / total_solicitado) * 100 if total_solicitado > 0 else 0
   ```

#### Notificaciones (Opcional)

- Alertar cuando una requisición se complete al 100%
- Notificar cuando pasen X días sin movimiento en requisiciones en proceso
- Email automático al solicitante al completarse

---

## Flujo de Usuario

### Para el Personal de Almacén:

1. Acceder al módulo "Surtir Requisiciones"
2. Ver lista de requisiciones pendientes/en proceso
3. Seleccionar una requisición
4. Ver detalle de productos y cantidades pendientes
5. Registrar entrega de productos disponibles
6. Sistema actualiza automáticamente los porcentajes
7. Si un producto no se puede completar, marcarlo como "Parcial Final"

### Para el Solicitante:

1. Crear requisición (flujo actual)
2. En "Mis Requisiciones", ver progreso en tiempo real
3. Recibir notificación cuando se complete
4. Ver historial de entregas de cada producto

---

## Consideraciones Técnicas

### Migración de Datos Existentes

```python
# Script de migración
from app_PDF_maker.models import Requisicion_detalle

for detalle in Requisicion_detalle.objects.all():
    if detalle.surtido:
        detalle.cantidad_surtida = detalle.cantidad
        detalle.porcentaje_completado = 100
        detalle.estado_surtido = 'COMPLETADO'
    else:
        detalle.cantidad_surtida = 0
        detalle.porcentaje_completado = 0
        detalle.estado_surtido = 'PENDIENTE'
    detalle.cantidad_solicitada = detalle.cantidad
    detalle.save()
```

### Compatibilidad con Sistema Actual

- Mantener campo `surtido` como booleano calculado:
  ```python
  @property
  def surtido(self):
      return self.estado_surtido == 'COMPLETADO'
  ```

- Esto asegura que el código existente siga funcionando

### Performance

- Indexar campos: `estado_surtido`, `porcentaje_completado`
- Caché para cálculos de progreso de requisiciones grandes
- Paginación en listados de requisiciones

---

## Plan de Implementación Sugerido

### Fase 1: Backend (Día 1)
- [ ] Modificar modelo `Requisicion_detalle`
- [ ] Crear modelo `HistorialSurtido`
- [ ] Crear y ejecutar migraciones
- [ ] Implementar lógica de cálculo de porcentajes
- [ ] Crear endpoints API
- [ ] Pruebas unitarias

### Fase 2: Frontend (Día 2)
- [ ] Crear vista de módulo de surtido
- [ ] Implementar formulario de registro de entregas
- [ ] Agregar visualización de progreso en listados
- [ ] Dashboard de métricas
- [ ] Integración con API

### Fase 3: Testing y Refinamiento (Día 3)
- [ ] Pruebas de integración
- [ ] Casos edge (sobre-surtido, cancelaciones, etc.)
- [ ] Ajustes de UI/UX
- [ ] Documentación de usuario
- [ ] Despliegue

---

## Alternativas Evaluadas

### Opción A: Registros Duplicados
**Descripción:** Crear un registro por cada entrega parcial  
**Pros:** Historial automático  
**Contras:** Complejidad en agregaciones, duplicados confusos  
**Decisión:** ❌ Descartada

### Opción B: Campo de cantidad_surtida + Tabla de Historial
**Descripción:** Mantener total surtido en el detalle + historial separado  
**Pros:** Simple, eficiente, historial completo  
**Contras:** Dos puntos de actualización  
**Decisión:** ✅ **Recomendada**

### Opción C: Sistema de Estados sin Historial
**Descripción:** Solo campos de cantidad sin registro de entregas  
**Pros:** Más simple  
**Contras:** Pérdida de trazabilidad  
**Decisión:** ❌ Descartada

---

## Métricas de Éxito

- ✅ Reducción de requisiciones "todo o nada"
- ✅ Visibilidad clara del progreso de surtido
- ✅ Trazabilidad completa de entregas
- ✅ Mejora en la gestión de inventario
- ✅ Satisfacción del usuario (tiempo de espera reducido)

---

## Notas Adicionales

- Esta funcionalidad podría integrarse con un sistema de notificaciones push
- Considerar permisos: ¿Quién puede registrar surtidos?
- Evaluar si se necesita firma digital o escaneo de códigos de barras
- Posible integración con sistema de almacén para actualización automática de stock

---

## Referencias

- Conversación con usuario: 22/12/2025
- Modelo actual: `Requisicion_detalle` con campo booleano `surtido`
- Ejemplo de datos: Producto duplicado con diferentes estados de surtido

---

**Última Actualización:** 22 de diciembre de 2025  
**Próxima Revisión:** Antes de iniciar implementación
