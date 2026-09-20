from decimal import Decimal

from rest_framework import serializers
from django.db.models import Sum

from ventas.models import Venta

from .models import CorteCaja, MovimientoCaja


class CorteCajaSerializer(
    serializers.ModelSerializer
):

    caja_nombre = serializers.CharField(
        source="caja.nombre",
        read_only=True
    )

    usuario_nombre = serializers.CharField(
        source="usuario.nombre",
        read_only=True
    )

    total_ventas = serializers.SerializerMethodField()
    numero_ventas = serializers.SerializerMethodField()
    total_reembolsos = serializers.SerializerMethodField()
    efectivo_esperado_actual = serializers.SerializerMethodField()

    class Meta:

        model = CorteCaja

        fields = [
            "id",
            "caja",
            "caja_nombre",
            "usuario",
            "usuario_nombre",
            "fecha_inicio",
            "fecha_fin",
            "efectivo_inicial",
            "efectivo_final",
            "diferencia",
            "total_ventas",
            "numero_ventas",
            "total_reembolsos",
            "efectivo_esperado_actual",
        ]

        read_only_fields = [
            "id",
            "caja_nombre",
            "usuario",
            "usuario_nombre",
            "fecha_inicio",
            "fecha_fin",
            "diferencia",
        ]

    def validate_efectivo_inicial(
        self,
        value
    ):

        if value < 0:

            raise serializers.ValidationError(
                "El efectivo inicial no puede ser negativo."
            )

        return value

    def validate_efectivo_final(
        self,
        value
    ):

        if value is not None and value < 0:

            raise serializers.ValidationError(
                "El efectivo final no puede ser negativo."
            )

        return value

    ESTADOS_VENTA_VALIDA = [
        "COMPLETADA",
        "DEVUELTA"
    ]

    def get_total_ventas(
        self,
        obj
    ):

        if hasattr(
            obj,
            "_total_ventas"
        ):

            return (
                obj._total_ventas
                or Decimal("0.00")
            )

        resultado = (
            Venta.objects
            .filter(
                corte_caja=obj,
                estado__in=self.ESTADOS_VENTA_VALIDA
            )
            .aggregate(
                total=Sum("total")
            )["total"]
        )

        return (
            resultado
            or Decimal("0.00")
        )

    def get_numero_ventas(
        self,
        obj
    ):

        if hasattr(
            obj,
            "_numero_ventas"
        ):

            return obj._numero_ventas

        return (
            Venta.objects
            .filter(
                corte_caja=obj,
                estado__in=self.ESTADOS_VENTA_VALIDA
            )
            .count()
        )

    def get_total_reembolsos(
        self,
        obj
    ):

        if hasattr(
            obj,
            "_total_reembolsos"
        ):

            return (
                obj._total_reembolsos
                or Decimal("0.00")
            )

        resultado = (
            MovimientoCaja.objects
            .filter(
                corte_caja=obj,
                tipo="REEMBOLSO"
            )
            .aggregate(
                total=Sum("monto")
            )["total"]
        )

        return (
            resultado
            or Decimal("0.00")
        )

    def get_efectivo_esperado_actual(
        self,
        obj
    ):

        if (
            hasattr(
                obj,
                "_total_efectivo_ventas"
            )
            and hasattr(
                obj,
                "_total_reembolsos_efectivo"
            )
        ):

            total_efectivo = (
                obj._total_efectivo_ventas
                or Decimal("0.00")
            )

            total_reembolsos_efectivo = (
                obj._total_reembolsos_efectivo
                or Decimal("0.00")
            )

            return (
                obj.efectivo_inicial
                + total_efectivo
                - total_reembolsos_efectivo
            )

        total_efectivo = (
            Venta.objects
            .filter(
                corte_caja=obj,
                estado__in=self.ESTADOS_VENTA_VALIDA,
                metodo_pago__nombre="EFECTIVO"
            )
            .aggregate(
                total=Sum("total")
            )["total"]
            or Decimal("0.00")
        )

        total_reembolsos_efectivo = (
            MovimientoCaja.objects
            .filter(
                corte_caja=obj,
                tipo="REEMBOLSO",
                metodo_pago__nombre="EFECTIVO"
            )
            .aggregate(
                total=Sum("monto")
            )["total"]
            or Decimal("0.00")
        )

        return (
            obj.efectivo_inicial
            + total_efectivo
            - total_reembolsos_efectivo
        )


class MovimientoCajaSerializer(
    serializers.ModelSerializer
):

    metodo_pago = serializers.CharField(
        source="metodo_pago.nombre",
        read_only=True
    )

    usuario = serializers.CharField(
        source="usuario.nombre",
        read_only=True
    )

    class Meta:

        model = MovimientoCaja

        fields = [
            "id",
            "corte_caja",
            "metodo_pago",
            "tipo",
            "monto",
            "devolucion",
            "observaciones",
            "usuario",
            "fecha",
        ]

        read_only_fields = [
            "id",
            "usuario",
            "fecha",
        ]