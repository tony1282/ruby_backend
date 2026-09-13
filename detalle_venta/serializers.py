from rest_framework import serializers

from .models import DetalleVenta


class DetalleVentaSerializer(serializers.ModelSerializer):

    class Meta:

        model = DetalleVenta

        fields = [
            "id",
            "venta",
            "variante",
            "cantidad",
            "precio_unitario",
            "descuento",
            "subtotal",
        ]

        read_only_fields = [
            "id",
            "venta",
            "variante",
            "cantidad",
            "precio_unitario",
            "descuento",
            "subtotal",
        ]