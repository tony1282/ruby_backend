from rest_framework import serializers

from .models import (
    Devolucion,
    DetalleDevolucion
)


class ProductoDevolucionSerializer(
    serializers.Serializer
):

    detalle_venta_id = serializers.UUIDField()

    cantidad = serializers.IntegerField(
        min_value=1
    )


class CrearDevolucionSerializer(
    serializers.Serializer
):

    venta_id = serializers.UUIDField()

    tipo = serializers.ChoiceField(
        choices=[
            "NORMAL",
            "DEFECTUOSO",
            "GARANTIA",
            "EXTRAORDINARIA"
        ]
    )

    motivo = serializers.CharField(
        allow_blank=False
    )
    metodo_pago_reembolso_id = serializers.UUIDField()


    productos = ProductoDevolucionSerializer(
        many=True,
        allow_empty=False
    )
    


class ActualizarDevolucionSerializer(
    serializers.Serializer
):

    tipo = serializers.ChoiceField(
        choices=[
            "NORMAL",
            "DEFECTUOSO",
            "GARANTIA",
            "EXTRAORDINARIA"
        ],
        required=False
    )

    motivo = serializers.CharField(
        allow_blank=False,
        required=False
    )

    metodo_pago_reembolso_id = serializers.UUIDField(
        required=False
    )
    

class DetalleDevolucionSerializer(
    serializers.ModelSerializer
):

    producto = serializers.CharField(
        source="detalle_venta.variante.producto.nombre",
        read_only=True
    )

    variante = serializers.CharField(
        source="detalle_venta.variante.nombre",
        read_only=True
    )

    class Meta:

        model = DetalleDevolucion

        fields = [
            "id",
            "producto",
            "variante",
            "cantidad",
            "precio_original",
            "subtotal"
        ]

        read_only_fields = [
            "id",
            "producto",
            "variante",
            "cantidad",
            "precio_original",
            "subtotal"
        ]


class DevolucionSerializer(
    serializers.ModelSerializer
):

    venta = serializers.CharField(
        source="venta.folio",
        read_only=True
    )

    usuario = serializers.CharField(
        source="usuario.nombre",
        read_only=True
    )

    metodo_pago_reembolso = serializers.CharField(
        source="metodo_pago_reembolso.nombre",
        allow_null=True,
        read_only=True
    )

    detalles = DetalleDevolucionSerializer(
        many=True,
        read_only=True
    )

    class Meta:

        model = Devolucion

        fields = [
            "id",
            "venta",
            "usuario",
            "metodo_pago_reembolso",
            "tipo",
            "motivo",
            "estado",
            "total_devuelto",
            "fecha",
            "detalles"
        ]

        read_only_fields = [
            "id",
            "venta",
            "usuario",
            "metodo_pago_reembolso",
            "estado",
            "total_devuelto",
            "fecha",
            "detalles"
        ]
        
class DetalleVentaParaDevolucionSerializer(serializers.Serializer):
    detalle_venta_id = serializers.UUIDField()
    variante_id = serializers.UUIDField()
    producto = serializers.CharField()
    variante = serializers.CharField()
    vendido = serializers.IntegerField()
    devuelto = serializers.IntegerField()
    en_garantia = serializers.IntegerField()
    disponible_devolucion = serializers.IntegerField()


class VentaParaDevolucionSerializer(serializers.Serializer):
    folio = serializers.CharField()
    fecha = serializers.DateTimeField()
    usuario = serializers.CharField()
    estado = serializers.CharField()
    metodo_pago = serializers.CharField()
    productos = DetalleVentaParaDevolucionSerializer(many=True)
    