from rest_framework import serializers

from .models import MovimientoInventario


class MovimientoInventarioSerializer(
    serializers.ModelSerializer
):

    variante = serializers.CharField(
        source="variante.nombre",
        read_only=True,
    )

    variante_id = serializers.UUIDField(
        source="variante.id",
        read_only=True,
    )

    usuario = serializers.CharField(
        source="usuario.nombre",
        read_only=True,
    )

    class Meta:

        model = MovimientoInventario

        fields = [
            "id",

            "variante_id",
            "variante",
            "tipo",

            "stock_anterior",
            "cantidad",
            "stock_nuevo",

            "stock_defectuoso_anterior",
            "stock_defectuoso_nuevo",

            "observaciones",
            "usuario",
            "fecha",
        ]

        read_only_fields = [
            "id",

            "variante_id",
            "variante",
            "tipo",

            "stock_anterior",
            "cantidad",
            "stock_nuevo",

            "stock_defectuoso_anterior",
            "stock_defectuoso_nuevo",

            "observaciones",
            "usuario",
            "fecha",
        ]

