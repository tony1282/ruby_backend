import uuid

from django.db import models

from variantes.models import Variante
from usuarios.models import Usuario

class MovimientoInventario(models.Model):
    TIPOS = [
        ("ENTRADA", "Entrada"),
        ("SALIDA", "Salida"),
        ("AJUSTE", "Ajuste"),
        ("DEVOLUCION", "Devolución"),
        ("GARANTIA", "Garantía"),
        ("CAMBIO_PRODUCTO", "Cambio de producto"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    variante = models.ForeignKey(
        Variante,
        on_delete=models.PROTECT,
        related_name="movimientos"
    )

    tipo = models.CharField(
        max_length=30,
        choices=TIPOS
    )

# ==========================================================
# STOCK VENDIBLE
# ==========================================================

    stock_anterior = models.PositiveIntegerField(
        default=0
    )

    cantidad = models.PositiveIntegerField(
        default=0
    )

    stock_nuevo = models.PositiveIntegerField(
        default=0
    )

# ==========================================================
# STOCK DEFECTUOSO
# ==========================================================

    stock_defectuoso_anterior = models.PositiveIntegerField(
        default=0
    )

    stock_defectuoso_nuevo = models.PositiveIntegerField(
        default=0
    )

    observaciones = models.TextField(
        blank=True,
        null=True
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="movimientos_inventario"
    )

    fecha = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["-fecha"],
                name="mov_inv_fecha_idx"
                ),
            models.Index(
                fields=["variante", "-fecha"],
                name="mov_inv_var_fecha_idx"
            ),
        ]

    def __str__(self):
        return (
            f"{self.tipo} - "
            f"{self.variante.nombre} - "
            f"{self.cantidad}"
        )
