from django.db import models
import uuid

from categorias.models import Categoria


class Producto(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos"
    )

    nombre = models.CharField(
        max_length=150
    )

    descripcion = models.TextField(
        blank=True,
        null=True
    )

    activo = models.BooleanField(
        default=True
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                models.functions.Lower("nombre"),
                name="producto_nombre_lower_unico",
            ),
        ]

    def __str__(self):
        return self.nombre