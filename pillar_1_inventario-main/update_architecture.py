def create_architecture_file():
    """
    Crea o actualiza el archivo ARCHITECTURE.md con la documentación actualizada.
    """
    content = """# 📋 Sistema de Gestión de Inventario - Documentación de Arquitectura

## 🔄 Ciclo de Vida de la Requisición

```mermaid
graph TD
    A[Inicio] --> B[Solicitud]
    B --> C[Validación]
    C --> D[Aprobación]
    D --> E[Entrega Parcial]
    D --> F[Entrega Total]
    E --> G[Devolución]
    F --> H[Cierre]
    G --> H
```

## 📝 Pasos para Llenar una Requisición

1. **Datos Generales**:
   - Seleccionar obra y ubicación
   - Especificar especialidad (plomería, electricidad, etc.)
   - Ingresar datos del solicitante

2. **Detalle de Materiales** (Máximo 14):
   - Seleccionar producto del catálogo
   - Especificar cantidad
   - Seleccionar unidad de medida
   - Agregar descripción (opcional)

3. **Revisión**:
   - Validar datos ingresados
   - Adjuntar imagen de respaldo
   - Confirmar requisición

4. **Autorización**:
   - Aprobación del supervisor
   - Validación de almacén
   - Generación de PDF

## 🤖 Módulo de Bot de Telegram

### Características Principales
- Registro de usuarios mediante comando `/start`
- Consulta de inventario en tiempo real
- Creación de requisiciones por chat
- Notificaciones de estado
- Soporte para imágenes y documentos

### Comandos Disponibles
- `/start` - Iniciar sesión/registrarse
- `/nueva` - Crear nueva requisición
- `/estado` - Consultar estado de requisiciones
- `/inventario` - Ver disponibilidad
- `/ayuda` - Mostrar ayuda

## 🌐 Módulo Web (Próximamente)

### Características Planificadas
- Panel de control interactivo
- Gestión completa de inventario
- Reportes y estadísticas
- Integración con el bot de Telegram
- Dashboard en tiempo real

### Tecnologías a Utilizar
- **Frontend**: React.js con Material-UI
- **Backend**: Django REST Framework
- **Base de Datos**: PostgreSQL
- **Autenticación**: JWT + OAuth2
- **Despliegue**: Docker + Nginx

## 🛠️ Estructura del Proyecto

```
pillar_1_inventario/
├── Almacen/                  # Aplicación principal
│   ├── models/               # Modelos de datos
│   ├── views/                # Vistas y lógica de negocio
│   ├── templates/            # Plantillas HTML
│   └── telegram_bot/         # Módulo del bot de Telegram
├── Inventario/               # Configuración del proyecto
└── documentacion/            # Documentación del proyecto
```

## 🔄 Flujo de Trabajo

1. **Solicitante**:
   - Crea la requisición vía web o bot
   - Adjunta documentación
   - Envía para revisión

2. **Supervisor**:
   - Recibe notificación
   - Revisa y aprueba/rechaza
   - Asigna prioridad

3. **Almacén**:
   - Prepara los materiales
   - Actualiza inventario
   - Registra salidas

4. **Sistema**:
   - Genera comprobantes
   - Actualiza reportes
   - Envía notificaciones
"""

    try:
        with open('documentacion/ARCHITECTURE.md', 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ ARCHITECTURE.md ha sido actualizado exitosamente.")
    except Exception as e:
        print(f"❌ Error al actualizar el archivo: {str(e)}")
        print("Asegúrate de que el directorio 'documentacion' existe y tienes permisos de escritura.")

if __name__ == "__main__":
    create_architecture_file()
