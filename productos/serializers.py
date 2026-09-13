from rest_framework import serializers

from categorias.models import Categoria

from .models import Producto


class ProductoSerializer(
    serializers.ModelSerializer
):

    categoria = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(),
        error_messages={
            "required": (
                "La categoría es obligatoria."
            ),
            "null": (
                "La categoría es obligatoria."
            ),
            "does_not_exist": (
                "La categoría seleccionada no existe."
            ),
            "incorrect_type": (
                "La categoría seleccionada no es válida."
            ),
        },
    )

    categoria_nombre = serializers.CharField(
        source="categoria.nombre",
        read_only=True,
    )

    nombre = serializers.CharField(
        max_length=150,
        error_messages={
            "required": (
                "El nombre del producto es obligatorio."
            ),
            "blank": (
                "El nombre del producto es obligatorio."
            ),
            "max_length": (
                "El nombre del producto no puede superar "
                "los 150 caracteres."
            ),
        },
    )

    descripcion = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        error_messages={
            "invalid": (
                "La descripción no es válida."
            ),
        },
    )

    class Meta:

        model = Producto

        fields = [
            "id",
            "categoria",
            "categoria_nombre",
            "nombre",
            "descripcion",
            "activo",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

        read_only_fields = [
            "id",
            "categoria_nombre",
            "activo",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

    # ==========================================================
    # VALIDACIONES GENERALES
    # ==========================================================

    def validate(
        self,
        attrs,
    ):

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
    # CATEGORIA
    # ==========================================================

    def validate_categoria(
        self,
        value,
    ):

        if not value.activo:

            raise serializers.ValidationError(
                "No se puede utilizar una categoría inactiva."
            )

        return value

    # ==========================================================
    # NOMBRE
    # ==========================================================

    def validate_nombre(
        self,
        value,
    ):

        value = value.strip()

        if not value:

            raise serializers.ValidationError(
                "El nombre del producto es obligatorio."
            )

        if len(value) > 150:

            raise serializers.ValidationError(
                "El nombre del producto no puede superar "
                "los 150 caracteres."
            )

        queryset = Producto.objects.filter(
            nombre__iexact=value
        )

        if self.instance:

            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():

            raise serializers.ValidationError(
                "Ya existe un producto con este nombre."
            )

        return value