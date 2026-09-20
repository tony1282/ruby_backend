import uuid

from django.db import models
from django.conf import settings

from cajas.models import Caja


class CorteCaja(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    caja = models.ForeignKey(
        Caja,
        on_delete=models.PROTECT,
        related_name="cortes"
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cortes"
    )

    fecha_inicio = models.DateTimeField(
        auto_now_add=True
    )

    fecha_fin = models.DateTimeField(
        null=True,
        blank=True
    )

    efectivo_inicial = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    efectivo_final = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    diferencia = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["fecha_inicio"],
                name="corte_fecha_inicio_idx"
            ),
            models.Index(
                fields=["caja", "fecha_fin"],
                name="corte_caja_fecha_fin_idx"
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["caja"],
                condition=models.Q(
                    fecha_fin__isnull=True
                ),
                name="corte_caja_unico_abierto",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    efectivo_inicial__gte=0
                ),
                name="corte_efectivo_inicial_no_negativo",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(efectivo_final__gte=0)
                    | models.Q(efectivo_final__isnull=True)
                ),
                name="corte_efectivo_final_no_negativo",
            ),
        ]

    def __str__(self):
        return f"Corte {self.id}"
    
    
    

class MovimientoCaja(models.Model):

    TIPOS = [
        ("REEMBOLSO", "Reembolso"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    corte_caja = models.ForeignKey(
        CorteCaja,
        on_delete=models.PROTECT,
        related_name="movimientos"
    )

    metodo_pago = models.ForeignKey(
        "metodos_pago.MetodoPago",
        on_delete=models.PROTECT,
        related_name="movimientos_caja"
    )

    tipo = models.CharField(
        max_length=30,
        choices=TIPOS
    )

    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    devolucion = models.OneToOneField(
        "devoluciones.Devolucion",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimiento_caja"
    )

    observaciones = models.TextField(
        blank=True,
        null=True
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="movimientos_caja"
    )

    fecha = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["fecha"],
                name="mov_caja_fecha_idx"
            ),
            models.Index(
                fields=["corte_caja", "tipo"],
                name="mov_caja_corte_tipo_idx"
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    monto__gte=0
                ),
                name="mov_caja_monto_no_negativo",
            ),
        ]

    def __str__(self):
        return f"{self.tipo} - ${self.monto}"