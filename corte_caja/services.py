import uuid
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from cajas.models import Caja
from ventas.models import Venta
from bitacora.services import registrar_bitacora
from config.exceptions import BusinessException

from .models import CorteCaja, MovimientoCaja


_Q = Decimal("0.01")


# ==============================================================
# VALIDACIONES COMUNES
# ==============================================================

def validar_uuid_caja(caja_id):

    if not caja_id:
        raise BusinessException(
            "El parámetro caja_id es obligatorio."
        )

    try:
        uuid.UUID(str(caja_id))
    except (TypeError, ValueError, AttributeError):
        raise BusinessException(
            "El identificador de la caja no es un UUID válido."
        )


def validar_efectivo(valor, nombre):

    if valor is None:
        raise BusinessException(
            f"El {nombre} es obligatorio."
        )

    try:
        monto = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        raise BusinessException(
            f"El {nombre} no es un valor numérico válido."
        )

    if not monto.is_finite():
        raise BusinessException(
            f"El {nombre} no es un valor válido."
        )

    if monto < 0:
        raise BusinessException(
            f"El {nombre} no puede ser negativo."
        )

    return monto.quantize(
        _Q,
        rounding=ROUND_HALF_UP
    )


# ==============================================================
# ABRIR CAJA
# ==============================================================

@transaction.atomic
def abrir_caja(caja_id, efectivo_inicial_raw, usuario):

    validar_uuid_caja(caja_id)

    efectivo_inicial = validar_efectivo(
        efectivo_inicial_raw,
        "efectivo inicial"
    )

    try:
        caja = Caja.objects.select_for_update().get(
            id=caja_id
        )
    except Caja.DoesNotExist:
        raise BusinessException(
            "La caja no existe."
        )

    if not usuario.activo:
        raise BusinessException(
            "El usuario no está activo y no puede abrir la caja."
        )

    if not caja.activa:
        raise BusinessException(
            "La caja está inactiva y no puede abrirse."
        )

    if CorteCaja.objects.filter(
        caja=caja,
        fecha_fin__isnull=True
    ).exists():

        raise BusinessException(
            "Ya existe un corte abierto para esta caja."
        )

    corte = CorteCaja.objects.create(
        caja=caja,
        usuario=usuario,
        efectivo_inicial=efectivo_inicial,
    )

    caja.estado = Caja.ESTADO_ABIERTA

    caja.save(
        update_fields=[
            "estado"
        ]
    )

    registrar_bitacora(
        usuario=usuario,
        modulo="Caja",
        accion="APERTURA_CAJA",
        descripcion=(
            f"Caja '{caja.nombre}' abierta correctamente por "
            f"{usuario.nombre} {usuario.apellido}. "
            f"Efectivo inicial: ${efectivo_inicial:.2f}"
        ),
    )

    return corte


# ==============================================================
# CERRAR CAJA
# ==============================================================

ESTADOS_VENTA_VALIDA = [
    "COMPLETADA",
    "DEVUELTA"
]


@transaction.atomic
def cerrar_caja(
    caja_id,
    efectivo_final_raw,
    usuario
):

    validar_uuid_caja(caja_id)

    efectivo_final = validar_efectivo(
        efectivo_final_raw,
        "efectivo final"
    )

    # ----------------------------------------------------------
    # LOCK GLOBAL:
    #
    # Siempre:
    #
    # Caja → CorteCaja
    #
    # Esto mantiene el mismo orden utilizado por crear_venta().
    # ----------------------------------------------------------

    try:
        caja = (
            Caja.objects
            .select_for_update()
            .get(id=caja_id)
        )
    except Caja.DoesNotExist:
        raise BusinessException(
            "La caja no existe."
        )

    if not usuario.activo:
        raise BusinessException(
            "El usuario está inactivo y no puede cerrar la caja."
        )

    if not caja.activa:
        raise BusinessException(
            "La caja está inactiva y no puede cerrarse."
        )

    if caja.estado != Caja.ESTADO_ABIERTA:
        raise BusinessException(
            "La caja no se encuentra en estado abierta."
        )

    try:
        corte = (
            CorteCaja.objects
            .select_for_update()
            .get(
                caja=caja,
                fecha_fin__isnull=True
            )
        )
    except CorteCaja.DoesNotExist:
        raise BusinessException(
            "No existe un corte abierto."
        )

    # ----------------------------------------------------------
    # VALIDAR PERMISOS DE CIERRE
    # ----------------------------------------------------------

    if (
        usuario.rol not in (0, 1)
        and corte.usuario_id != usuario.id
    ):

        raise BusinessException(
            "Solo puedes cerrar la caja que tú abriste."
        )

    # ----------------------------------------------------------
    # TOTAL DE VENTAS EN EFECTIVO
    # ----------------------------------------------------------

    total_ventas_efectivo = (
        Venta.objects
        .filter(
            corte_caja=corte,
            metodo_pago__nombre="EFECTIVO",
            estado__in=ESTADOS_VENTA_VALIDA
        )
        .aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )

    total_ventas_efectivo = total_ventas_efectivo.quantize(
        _Q,
        rounding=ROUND_HALF_UP
    )

    # ----------------------------------------------------------
    # TOTAL DE REEMBOLSOS EN EFECTIVO
    # ----------------------------------------------------------

    total_reembolsos_efectivo = (
        MovimientoCaja.objects
        .filter(
            corte_caja=corte,
            metodo_pago__nombre="EFECTIVO",
            tipo="REEMBOLSO"
        )
        .aggregate(
            total=Sum("monto")
        )["total"]
        or Decimal("0.00")
    )

    total_reembolsos_efectivo = (
        total_reembolsos_efectivo.quantize(
            _Q,
            rounding=ROUND_HALF_UP
        )
    )

    # ----------------------------------------------------------
    # EFECTIVO ESPERADO
    # ----------------------------------------------------------

    efectivo_esperado = (
        corte.efectivo_inicial
        + total_ventas_efectivo
        - total_reembolsos_efectivo
    ).quantize(
        _Q,
        rounding=ROUND_HALF_UP
    )

    # ----------------------------------------------------------
    # DIFERENCIA
    # ----------------------------------------------------------

    diferencia = (
        efectivo_final
        - efectivo_esperado
    ).quantize(
        _Q,
        rounding=ROUND_HALF_UP
    )

    # ----------------------------------------------------------
    # CERRAR CORTE
    # ----------------------------------------------------------

    corte.efectivo_final = efectivo_final
    corte.diferencia = diferencia
    corte.fecha_fin = timezone.now()

    corte.save(
        update_fields=[
            "efectivo_final",
            "diferencia",
            "fecha_fin"
        ]
    )

    # ----------------------------------------------------------
    # ACTUALIZAR ESTADO DE LA CAJA
    # ----------------------------------------------------------

    caja.estado = Caja.ESTADO_CERRADA

    caja.save(
        update_fields=[
            "estado"
        ]
    )

    # ----------------------------------------------------------
    # BITÁCORA
    # ----------------------------------------------------------

    registrar_bitacora(
        usuario=usuario,
        modulo="Caja",
        accion="CIERRE_CAJA",
        descripcion=(
            f"Caja '{caja.nombre}' cerrada correctamente por "
            f"{usuario.nombre} {usuario.apellido}. "
            f"Efectivo esperado: ${efectivo_esperado:.2f}. "
            f"Efectivo contado: ${efectivo_final:.2f}. "
            f"Diferencia: ${diferencia:.2f}"
        ),
    )

    return (
        corte,
        efectivo_esperado,
        diferencia
    )