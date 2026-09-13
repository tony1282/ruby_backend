from rest_framework import serializers

from .models import Venta


class VentaSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = Venta

        fields = [
            "id",
            "folio",
            "usuario",
            "corte_caja",
            "metodo_pago",
            "fecha",
            "subtotal",
            "descuento",
            "iva",
            "total",
            "estado",
        ]

        read_only_fields = [
            "id",
            "folio",
            "usuario",
            "corte_caja",
            "metodo_pago",
            "fecha",
            "subtotal",
            "descuento",
            "iva",
            "total",
            "estado",
        ]