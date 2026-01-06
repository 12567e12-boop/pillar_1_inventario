from django.db import models, transaction
from django.conf import settings
from datetime import date
from django.utils import timezone
from .estados import aplicar_transicion
from Almacen.models.movimientos.movimientos import Inventario, Registro

import uuid


class Requisicion(models.Model):
    # --- Identificación ---
    id = models.CharField(max_length=30, primary_key=True, editable=False)
    token_publico = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # --- Información básica ---
    obra = models.CharField(max_length=200, default="Obra sin especificar")
    ubicacion = models.CharField(max_length=200, default="Ubicación no definida")
    especialidad = models.CharField(max_length=100, default="General")
    solicitante_nombre = models.CharField(max_length=200, blank=True, null=True, help_text="Nombre del solicitante cuando no está vinculado a un empleado")

    # 🔗 Relaciones
    bloque = models.ForeignKey("Almacen.Bloque", on_delete=models.CASCADE, null=True, blank=True)
    solicitante = models.ForeignKey("Almacen.Empleado", on_delete=models.CASCADE, null=True, blank=True, related_name='requisiciones_solicitadas')
    supervisor = models.ForeignKey(
        "Almacen.Empleado", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='requisiciones_supervisadas',
        help_text="Supervisor asignado para revisar esta requisición"
    )

    # --- Fechas ---
    fecha_soli = models.DateField(default=date.today)
    fecha_util = models.DateField(null=True, blank=True)
    fecha_surt = models.DateField(null=True, blank=True)

    # --- Usuario ---
    usuario_creador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    # --- Autorizaciones ---
    autorizado_supervisor = models.BooleanField(default=False)
    autorizado_directivo = models.BooleanField(default=False)

    # --- Estado general ---
    estado = models.CharField(
        max_length=30,
        default="pendiente",
        help_text="Estados: pendiente / supervisor / autorizada / rechazada / surtida / cerrada"
    )

    # --- Información adicional ---
    observaciones = models.TextField(blank=True, null=True)
    numero_de_articulos = models.IntegerField(default=0)
    imagen = models.ImageField(upload_to='requisiciones/', blank=False, null=False, default='requisiciones/default.jpg', help_text="Imagen obligatoria adjunta a la requisición")

    # --------------------------------------------------------
    # REPRESENTACIÓN
    # --------------------------------------------------------
    def __str__(self):
        return f"{self.id or 'SIN-FOLIO'} - {self.obra}"

    # --------------------------------------------------------
    # 🔧 GENERACIÓN DE ID — al crear la requisición
    # --------------------------------------------------------
    def generar_id(self):
        bloque_part = (self.bloque.nombre[:3].upper() if self.bloque else "XXX")
        ubicacion_part = (self.ubicacion[:3].upper() if self.ubicacion else "LOC")
        especialidad_part = (self.especialidad[:3].upper() if self.especialidad else "GEN")

        # Encontrar el número más alto existente para evitar conflictos
        max_num = 0
        for req in Requisicion.objects.all():
            try:
                parts = req.id.split('-')
                if len(parts) >= 3:
                    num = int(parts[2])
                    if num > max_num:
                        max_num = num
            except (ValueError, IndexError):
                continue
        consecutivo = max_num + 1
        self.id = f"{bloque_part}-{ubicacion_part}-{consecutivo:04d}-{especialidad_part}"

    # --------------------------------------------------------
    # 🧩 MÉTODOS DE ESTADO
    # --------------------------------------------------------

    def aprobar_supervisor(self, supervisor=None, usuario=None):
        """
        Aprueba la requisición como supervisor.
        
        Args:
            supervisor: Objeto Empleado del supervisor que aprueba
            usuario: Usuario del sistema que realiza la acción (opcional)
            
        Raises:
            ValueError: Si la requisición no está en estado 'pendiente' o el supervisor no tiene permiso
        """
        if self.estado != "pendiente":
            raise ValueError(f"No se puede aprobar una requisición en estado '{self.estado}'.")
        
        # Verificar que el supervisor que aprueba sea el asignado
        if supervisor and self.supervisor and self.supervisor.id != supervisor.id:
            raise ValueError("No tienes permiso para aprobar esta requisición.")
            
        self.autorizado_supervisor = True
        self.estado = "supervisor"
        
        # Si se proporciona un usuario, guardar como usuario_creador
        if usuario and not self.usuario_creador:
            self.usuario_creador = usuario
            self.save(update_fields=["autorizado_supervisor", "estado", "usuario_creador"])
        else:
            self.save(update_fields=["autorizado_supervisor", "estado"])

    def aprobar_directivo(self, usuario=None):
        """
        Cuando el directivo aprueba, se actualiza el estado a 'autorizada'.
        
        Args:
            usuario: Usuario que aprueba (opcional)
        """
        if not self.autorizado_supervisor:
            raise ValueError("El supervisor debe autorizar primero.")
            
        if self.estado != 'supervisor':
            raise ValueError(f"La requisición debe estar en estado 'supervisor', no en '{self.estado}'")
            
        # Transacción atómica: si algo falla, se revierte todo
        with transaction.atomic():
            self.autorizado_directivo = True
            self.estado = "autorizada"
            
            # Si se proporciona un usuario, actualizar el usuario creador si no existe
            if usuario and not self.usuario_creador:
                self.usuario_creador = usuario
                update_fields = ["autorizado_directivo", "estado", "usuario_creador"]
            else:
                update_fields = ["autorizado_directivo", "estado"]
            
            # Guardar los cambios en la requisición
            self.save(update_fields=update_fields)

            # Descontar inventario
            for det in self.detalles.all():
                if not hasattr(det, 'producto') or not det.producto:
                    continue
                    
                inventario = Inventario.objects.filter(
                    bloque=self.bloque,
                    producto=det.producto
                ).first()

                if not inventario:
                    raise ValueError(f"No existe inventario para {getattr(det.producto, 'nombre', 'el producto seleccionado')} en este bloque.")
                
                if inventario.cantidad < det.cantidad:
                    raise ValueError(f"Stock insuficiente para {getattr(det.producto, 'nombre', 'el producto seleccionado')}. Disponible: {inventario.cantidad}, Solicitado: {det.cantidad}")

                inventario.cantidad -= det.cantidad
                inventario.save()

                # Registrar el movimiento
                Registro.objects.create(
                    bloque=self.bloque,
                    empleado=self.solicitante,
                    producto=det.producto,
                    cantidad=det.cantidad,
                    tipo='salida',
                    usuario=self.usuario_creador
                )

    def rechazar(self, motivo="Sin especificar"):
        if self.estado in ["rechazada", "cerrada"]:
            raise ValueError(f"No se puede rechazar una requisición en estado '{self.estado}'.")
        self.estado = "rechazada"
        self.observaciones = motivo
        self.save(update_fields=["estado", "observaciones"])

    def marcar_surtida(self):
        """Solo cambia el estado, sin modificar inventario."""
        if self.estado != "autorizada":
            raise ValueError("Solo se puede marcar como surtida si fue autorizada.")
        self.estado = "surtida"
        self.fecha_surt = date.today()
        self.save(update_fields=["estado", "fecha_surt"])

    def cerrar(self):
        self.estado = "cerrada"
        self.save(update_fields=["estado"])

    # --------------------------------------------------------
    # 📊 UTILITARIOS
    # --------------------------------------------------------
    @property
    def puede_surtirse(self):
        return self.estado == "autorizada"

    @property
    def esta_activa(self):
        return self.estado not in ["cerrada", "rechazada"]
