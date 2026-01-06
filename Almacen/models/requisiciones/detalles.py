from django.db import models
from Almacen.models.base.base import Producto, Unidad
from .requisiciones import Requisicion

class DetalleRequisicion(models.Model):
    requisicion = models.ForeignKey(Requisicion, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    unidad = models.ForeignKey(Unidad, on_delete=models.SET_NULL, null=True)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    comentario = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.producto.nombre} ({self.cantidad} {self.unidad})"
