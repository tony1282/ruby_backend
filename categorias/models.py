from django.db import models
from django.db.models.functions import Lower
import uuid


class Categoria(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    nombre = models.CharField(
        max_length=100,
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
                Lower("nombre"),
                name="categoria_nombre_ci_unique"
            )
        ]

        indexes = [
            models.Index(
                fields=["activo"],
                name="categorias_activo_idx"
            ),
        ]

    def __str__(self):
        return self.nombre