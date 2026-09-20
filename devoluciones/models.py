from django.db import models
import uuid

from ventas.models import Venta
from detalle_venta.models import DetalleVenta
from usuarios.models import Usuario

from metodos_pago.models import MetodoPago


class Devolucion(models.Model):

    TIPO_CHOICES = (
        ("NORMAL", "Normal"),
        ("DEFECTUOSO", "Defectuoso"),
        ("GARANTIA", "Garantía"),
        ("EXTRAORDINARIA", "Extraordinaria"),
    )


    ESTADO_CHOICES = (
        ("PENDIENTE", "Pendiente"),
        ("APROBADA", "Aprobada"),
        ("RECHAZADA", "Rechazada"),
        ("CANCELADA", "Cancelada"),
    )



    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )


    venta = models.ForeignKey(
        Venta,
        on_delete=models.PROTECT,
        related_name="devoluciones"
    )
    
    metodo_pago_reembolso = models.ForeignKey(
        MetodoPago,
        on_delete=models.PROTECT,
        related_name="devoluciones_reembolsadas",
        null=True,
        blank=True
    )


    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="devoluciones"
    )


    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default="NORMAL"
    )


    motivo = models.TextField()


    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="PENDIENTE"
    )


    total_devuelto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )


    fecha = models.DateTimeField(
        auto_now_add=True
    )


    def __str__(self):
        return f"Devolución {self.id}"



class DetalleDevolucion(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    devolucion = models.ForeignKey(
        Devolucion,
        on_delete=models.CASCADE,
        related_name="detalles"
    )

    detalle_venta = models.ForeignKey(
        DetalleVenta,
        on_delete=models.PROTECT,
        related_name="devoluciones"
    )

    cantidad = models.PositiveIntegerField()

    precio_original = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["devolucion", "detalle_venta"],
                name="detalle_devolucion_unico_por_devolucion"
            ),
            models.CheckConstraint(
                condition=models.Q(cantidad__gte=1),
                name="detalle_devolucion_cantidad_positiva"
            ),
        ]

    def __str__(self):
        return f"Detalle devolución {self.id}"