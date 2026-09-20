from django.db import models
import uuid


class Empresa(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    singleton_key = models.BooleanField(
        default=True,
        unique=True,
        editable=False
    )

    nombre = models.CharField(
        max_length=150
    )

    rfc = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    direccion = models.TextField()

    telefono = models.CharField(
        max_length=30,
        null=True,
        blank=True
    )

    mensaje_ticket = models.TextField()

    iva = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    dias_devolucion = models.PositiveIntegerField()

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.nombre