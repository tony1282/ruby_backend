import re

from rest_framework import serializers

from .models import Empresa


class EmpresaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Empresa
        fields = [
            "id",
            "nombre",
            "rfc",
            "direccion",
            "telefono",
            "mensaje_ticket",
            "iva",
            "dias_devolucion",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = [
            "id",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

    def validate_nombre(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "El nombre de la empresa no puede estar vacío."
            )

        return value

    def validate_rfc(self, value):
        if value is None:
            return value

        value = value.strip().upper()

        if not value:
            return None

        patron = r"^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$"

        if not re.fullmatch(patron, value):
            raise serializers.ValidationError(
                "El RFC no tiene un formato válido."
            )

        return value

    def validate_telefono(self, value):
        if value is None:
            return value

        value = value.strip()

        if not re.fullmatch(r"\d{10}", value):
            raise serializers.ValidationError(
                "El teléfono debe contener exactamente 10 dígitos numéricos."
            )

        return value

    def validate_iva(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "El IVA no puede ser negativo."
            )

        if value > 100:
            raise serializers.ValidationError(
                "El IVA no puede ser mayor a 100."
            )

        return value

    def validate_dias_devolucion(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Los días de devolución no pueden ser negativos."
            )

        return value