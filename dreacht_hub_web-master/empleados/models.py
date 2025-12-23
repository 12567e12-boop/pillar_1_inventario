from django.db import models


# ==============================
# Empleado
# ==============================
class Empleado(models.Model):
    id_empleado = models.AutoField(primary_key=True, editable=False, unique=True, db_index=True)
    nombre = models.CharField(max_length=50)
    foto = models.ImageField()
    puesto = models.CharField(max_length=50)
    direccion = models.CharField(max_length=200, blank=True)
    nss = models.CharField(max_length=50, blank=True)
    tel = models.CharField(max_length=50, blank=True)
    tel_emg = models.CharField(max_length=50, blank=True)
    gafete_pdf = models.FileField(upload_to="gafetes/")
    fecha_alta = models.DateField(auto_now_add=True)
    fecha_baja = models.DateField(blank=True, null=True)
    id_nomina = models.OneToOneField('Nomina', on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.nombre


# ==============================
# Nómina
# ==============================
class Nomina(models.Model):
    fecha = models.DateField()
    descripcion = models.CharField(max_length=100)

    def __str__(self):
        return f"Nómina {self.fecha}"


# ==============================
# Requisición
# ==============================
class Requisicion(models.Model):
    id = models.CharField(max_length=30, primary_key=True, editable=False)
    obra = models.CharField(max_length=200, default="Obra sin especificar")
    ubicacion = models.CharField(max_length=200, default="Ubicación no definida")
    especialidad = models.CharField(max_length=100, default="General")
    solicitante_nombre = models.CharField(max_length=200, blank=True, null=True, help_text="Nombre del solicitante")
    
    # --- Relación con supervisor (almacen_empleado) ---
    supervisor_id_bigint = models.BigIntegerField(null=True, blank=True, help_text="ID del supervisor en almacen_empleado")
    
    # --- Fechas ---
    fecha_soli = models.DateField(null=True, blank=True)
    fecha_util = models.DateField(null=True, blank=True)
    fecha_surt = models.DateField(null=True, blank=True)
    
    # --- Información adicional ---
    numero_de_articulos = models.IntegerField(default=0)
    observaciones = models.TextField(blank=True, null=True)
    fecha_hora_creacion = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.id:
            obra_part = (self.obra[:4].upper()).ljust(4, 'X')
            especialidad_part = (self.especialidad[:3].upper()).ljust(3, 'X')
            fecha_part = self.fecha_soli.strftime('%Y%m%d') if self.fecha_soli else '00000000'
            self.id = f"{obra_part}{especialidad_part}{fecha_part}"
        super().save(*args, **kwargs)

    def actualizar_numero_de_articulos(self):
        """Actualiza automáticamente el número de artículos al guardar."""
        self.numero_de_articulos = self.detalles.count()
        self.save(update_fields=["numero_de_articulos"])

    def __str__(self):
        return f"Requisición {self.id} - {self.obra}"


# ==============================
# Material
# ==============================
class Material(models.Model):
    requisicion = models.ForeignKey(Requisicion, on_delete=models.CASCADE, related_name='materiales')
    material_id = models.CharField(max_length=50)
    tags = models.CharField(max_length=200)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    unidad = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiales"
        ordering = ["requisicion__fecha_soli"]

    def __str__(self):
        return f"{self.tags} ({self.cantidad} {self.unidad})"


# ==============================
# Detalle de Requisición
# ==============================
class DetalleRequisicion(models.Model):
    requisicion = models.ForeignKey(
        Requisicion,
        related_name="detalles",
        on_delete=models.CASCADE
    )
    material_no = models.PositiveIntegerField(editable=False)
    descripcion = models.CharField(max_length=255)
    unidad = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Detalle de requisición"
        verbose_name_plural = "Detalles de requisición"
        ordering = ["material_no"]

    def save(self, *args, **kwargs):
        """Asigna automáticamente el número de material y actualiza el total de artículos."""
        if not self.material_no:
            last = (
                DetalleRequisicion.objects.filter(requisicion=self.requisicion)
                .aggregate(models.Max("material_no"))
                .get("material_no__max")
            )
            self.material_no = (last or 0) + 1

        super().save(*args, **kwargs)

        # Actualizar contador en la requisición principal
        self.requisicion.actualizar_numero_de_articulos()

    def __str__(self):
        return f"Material {self.material_no}: {self.descripcion}"
