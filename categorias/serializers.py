from rest_framework import serializers

from .models import Categoria


class CategoriaSerializer(serializers.ModelSerializer):

    class Meta:

        model = Categoria

        fields = [
            "id",
            "nombre",
            "descripcion",
            "activo",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

        read_only_fields = [
            "id",
            "activo",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

        extra_kwargs = {
            "nombre": {
                "error_messages": {
                    "blank": "El nombre de la categoría es obligatorio.",
                    "max_length": "El nombre de la categoría no puede superar los 100 caracteres.",
                }
            }
        }

    # ==========================================================
    # VALIDACIÓN GENERAL
    # ==========================================================

    def validate(self, attrs):

        if "activo" in self.initial_data:

            raise serializers.ValidationError(
                {
                    "activo": (
                        "El estado activo no puede modificarse "
                        "directamente. Utiliza los endpoints "
                        "activar/desactivar."
                    )
                }
            )

        return attrs

    # ==========================================================
    # VALIDAR NOMBRE
    # ==========================================================

    def validate_nombre(self, value):

        value = value.strip()

        if not value:

            raise serializers.ValidationError(
                "El nombre de la categoría es obligatorio."
            )

        queryset = Categoria.objects.filter(
            nombre__iexact=value
        )

        if self.instance:

            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():

            raise serializers.ValidationError(
                "Ya existe una categoría con este nombre."
            )

        return value

    # ==========================================================
    # VALIDAR DESCRIPCIÓN
    # ==========================================================

    def validate_descripcion(self, value):

        if value is not None:

            value = value.strip()

        return value