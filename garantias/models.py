from django.db import models
import uuid

from ventas.models import Venta
from detalle_venta.models import DetalleVenta
from variantes.models import Variante
from usuarios.models import Usuario


class Garantia(models.Model):

    ESTADO_CHOICES = (
        ("PENDIENTE", "Pendiente"),
        ("APROBADA", "Aprobada"),
        ("RECHAZADA", "Rechazada"),
        ("FINALIZADA", "Finalizada"),
    )

    RESOLUCION_CHOICES = (
        ("REEMPLAZO", "Reemplazo"),
        ("CAMBIO_PRODUCTO", "Cambio de producto"),
        ("REPARACION", "Reparación"),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    venta = models.ForeignKey(
        Venta,
        on_delete=models.PROTECT,
        related_name="garantias"
    )

    detalle_venta = models.ForeignKey(
        DetalleVenta,
        on_delete=models.PROTECT,
        related_name="garantias"
    )

    # Variante original del producto en garantía
    variante = models.ForeignKey(
        Variante,
        on_delete=models.PROTECT,
        related_name="garantias"
    )

    # Cantidad de unidades que entran en esta garantía
    cantidad = models.PositiveIntegerField(
        default=1
    )

    # Variante entregada como reemplazo.
    # Solo aplica cuando la resolución es CAMBIO_PRODUCTO.
    variante_nueva = models.ForeignKey(
        Variante,
        on_delete=models.PROTECT,
        related_name="garantias_como_nueva",
        null=True,
        blank=True
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="garantias"
    )

    motivo = models.TextField()

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="PENDIENTE"
    )

    resolucion = models.CharField(
        max_length=20,
        choices=RESOLUCION_CHOICES,
        null=True,
        blank=True
    )

    observaciones = models.TextField(
        null=True,
        blank=True
    )

    fecha = models.DateTimeField(
        auto_now_add=True
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-fecha"]

        indexes = [
            models.Index(fields=["estado"]),
            models.Index(
                fields=["detalle_venta", "estado"],
                name="garantia_detalle_estado_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gte=1),
                name="garantia_cantidad_mayor_cero",
            ),
        ]

    def __str__(self):
        return f"Garantia {self.id} - {self.variante.nombre}"