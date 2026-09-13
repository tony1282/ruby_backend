from decimal import Decimal, ROUND_HALF_UP

from django.db import models, transaction
from django.utils import timezone

from ventas.models import Venta
from empresa.models import Empresa
from detalle_venta.models import DetalleVenta
from inventario.models import MovimientoInventario
from cajas.models import Caja
from corte_caja.models import MovimientoCaja, CorteCaja
from garantias.models import Garantia
from variantes.models import Variante
from bitacora.services import registrar_bitacora
from config.exceptions import BusinessException

from .models import Devolucion, DetalleDevolucion


_Q = Decimal("0.01")


def _redondear(valor):
    return valor.quantize(
        _Q,
        rounding=ROUND_HALF_UP
    )


# ============================================================
# HELPERS CREAR DEVOLUCIÓN
# ============================================================

def _validar_venta_devolucion(venta_id, usuario):



    
    try:

        venta = (
            Venta.objects
            .select_for_update()
            .get(id=venta_id)
        )

    except Venta.DoesNotExist:

        raise BusinessException(
            "La venta no existe."
        )

    if venta.estado == "CANCELADA":

        raise BusinessException(
            "No se puede devolver una venta cancelada."
        )

    if venta.estado == "DEVUELTA":

        raise BusinessException(
            "La venta ya fue devuelta completamente."
        )
        
    if usuario.rol not in (0, 1) and venta.usuario_id != usuario.id:
        raise BusinessException(
            "No tienes permisos para devolver esta venta."
        )

    return venta


def _validar_plazo(venta, tipo):

    if tipo != "NORMAL":
        return

    empresa = Empresa.objects.first()

    if not empresa:

        raise BusinessException(
            "No existe configuración de empresa."
        )

    if (
        timezone.now() - venta.fecha
    ).days > empresa.dias_devolucion:

        raise BusinessException(
            "El periodo de devolución expiró."
        )


def _calcular_factor_reembolso(venta):

    subtotal_bruto = (
        DetalleVenta.objects
        .filter(venta=venta)
        .aggregate(
            total=models.Sum("subtotal")
        )["total"]
        or Decimal("0.00")
    )

    subtotal_bruto = _redondear(
        subtotal_bruto
    )

    if subtotal_bruto <= 0:

        raise BusinessException(
            "La venta no tiene un subtotal válido."
        )

    return venta.subtotal / subtotal_bruto


def _disponible_para_devolucion(
    detalle_venta
):

    cantidad_devuelta = (
        DetalleDevolucion.objects
        .filter(
            detalle_venta=detalle_venta,
            devolucion__estado__in=[
                "PENDIENTE",
                "APROBADA"
            ]
        )
        .aggregate(
            total=models.Sum("cantidad")
        )["total"]
        or 0
    )

    cantidad_garantizada = (
        Garantia.objects
        .filter(
            detalle_venta=detalle_venta,
            estado__in=[
                "PENDIENTE",
                "APROBADA",
            ]
        )
        .aggregate(
            total=models.Sum("cantidad")
        )["total"]
        or 0
    )

    return max(
        detalle_venta.cantidad
        - cantidad_devuelta
        - cantidad_garantizada,
        0
    )


def _crear_detalles_devolucion(
    devolucion,
    venta,
    productos,
    factor_reembolso
):

    total = Decimal("0.00")

    for item in productos:

        try:

            detalle_venta = (
                DetalleVenta.objects
                .select_for_update()
                .get(
                    id=item["detalle_venta_id"],
                    venta=venta
                )
            )

        except DetalleVenta.DoesNotExist:

            raise BusinessException(
                "El producto no pertenece a la venta."
            )

        cantidad = item["cantidad"]

        if cantidad <= 0:

            raise BusinessException(
                "La cantidad debe ser mayor a cero."
            )

        disponible = (
            _disponible_para_devolucion(
                detalle_venta
            )
        )

        if cantidad > disponible:

            raise BusinessException(
                "La cantidad solicitada para devolución "
                "supera las unidades disponibles. "
                f"Disponibles: {disponible}."
            )

        subtotal_bruto = _redondear(
            cantidad * detalle_venta.precio_unitario
        )

        subtotal = _redondear(
            subtotal_bruto * factor_reembolso
        )

        DetalleDevolucion.objects.create(
            devolucion=devolucion,
            detalle_venta=detalle_venta,
            cantidad=cantidad,
            precio_original=detalle_venta.precio_unitario,
            subtotal=subtotal,
        )

        total += subtotal

    return _redondear(total)


def _calcular_total_devuelto(
    venta,
    total
):

    if total <= 0:

        raise BusinessException(
            "El importe de la devolución debe ser mayor que cero."
        )

    if venta.subtotal > 0:

        iva_devolucion = _redondear(
            (total * venta.iva) / venta.subtotal
        )

    else:

        iva_devolucion = Decimal("0.00")

    total_devuelto = _redondear(
        total + iva_devolucion
    )

    return min(
        total_devuelto,
        venta.total
    )


# ============================================================
# HELPERS APROBAR DEVOLUCIÓN
# ============================================================

def _validar_cantidades_aprobacion(detalles, devolucion):
    detalle_ids = [
        detalle.detalle_venta_id
        for detalle in detalles
    ]

    if not detalle_ids:
        return

    cantidades_devoluciones = (
        DetalleDevolucion.objects
        .filter(
            detalle_venta_id__in=detalle_ids,
            devolucion__estado__in=["APROBADA", "PENDIENTE"],
        )
        .exclude(
            devolucion_id=devolucion.id
        )
        .values("detalle_venta_id")
        .annotate(
            cantidad_aprobada=models.Sum(
                "cantidad",
                filter=models.Q(
                    devolucion__estado="APROBADA"
                ),
            ),
            cantidad_pendiente=models.Sum(
                "cantidad",
                filter=models.Q(
                    devolucion__estado="PENDIENTE"
                ),
            ),
        )
    )

    cantidades_devoluciones_map = {
        item["detalle_venta_id"]: {
            "aprobada": item["cantidad_aprobada"] or 0,
            "pendiente": item["cantidad_pendiente"] or 0,
        }
        for item in cantidades_devoluciones
    }

    cantidades_garantias = (
        Garantia.objects
        .filter(
            detalle_venta_id__in=detalle_ids,
            estado__in=["PENDIENTE", "APROBADA"],
        )
        .values("detalle_venta_id")
        .annotate(
            total=models.Sum("cantidad")
        )
    )

    cantidades_garantias_map = {
        item["detalle_venta_id"]: item["total"] or 0
        for item in cantidades_garantias
    }

    for detalle in detalles:
        detalle_venta = detalle.detalle_venta
        detalle_id = detalle.detalle_venta_id

        cantidades = cantidades_devoluciones_map.get(
            detalle_id,
            {
                "aprobada": 0,
                "pendiente": 0,
            },
        )

        cantidad_aprobada = cantidades["aprobada"]
        cantidad_pendiente = cantidades["pendiente"]

        cantidad_garantizada = cantidades_garantias_map.get(
            detalle_id,
            0,
        )

        disponible = max(
            detalle_venta.cantidad
            - cantidad_aprobada
            - cantidad_pendiente
            - cantidad_garantizada,
            0,
        )

        if detalle.cantidad > disponible:
            raise BusinessException(
                "La cantidad devuelta supera "
                "la cantidad disponible."
            )

   
def _obtener_corte_efectivo(caja, corte):
    if not caja.activa:
        raise BusinessException(
            "La caja está inactiva y no puede registrar el reembolso."
        )

    if caja.estado != Caja.ESTADO_ABIERTA:
        raise BusinessException(
            "La caja no se encuentra abierta para registrar el reembolso."
        )

    if not corte:
        raise BusinessException(
            "No existe un corte de caja abierto para registrar el reembolso."
        )

    if corte.fecha_fin is not None:
        raise BusinessException(
            "El corte de caja ya se encuentra cerrado."
        )

    return corte

    if not venta.corte_caja:
        raise BusinessException(
            "La venta no tiene un corte de caja asociado."
        )

    try:
        caja = (
            Caja.objects
            .select_for_update()
            .get(
                id=venta.corte_caja.caja_id
            )
        )
    except Caja.DoesNotExist:
        raise BusinessException(
            "La caja asociada a la venta no existe."
        )

    if not caja.activa:
        raise BusinessException(
            "La caja está inactiva y no puede registrar el reembolso."
        )

    if caja.estado != Caja.ESTADO_ABIERTA:
        raise BusinessException(
            "La caja no se encuentra abierta para registrar el reembolso."
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
            "No existe un corte de caja abierto "
            "para registrar el reembolso."
        )

    return corte

def _reponer_stock(
    detalles,
    devolucion,
    usuario
):

    for detalle in sorted(
        detalles,
        key=lambda detalle: str(
            detalle.detalle_venta_id
            )
    ):


        variante = (
            Variante.objects
            .select_for_update()
            .get(
                id=detalle.detalle_venta.variante_id
            )
        )

        stock_ant = variante.stock
        stock_def_ant = variante.stock_defectuoso

        if devolucion.tipo == "DEFECTUOSO":

            stock_nuevo = stock_ant

            stock_def_nuevo = (
                stock_def_ant
                + detalle.cantidad
            )

        else:

            stock_nuevo = (
                stock_ant
                + detalle.cantidad
            )

            stock_def_nuevo = stock_def_ant

        MovimientoInventario.objects.create(
            variante=variante,
            tipo="DEVOLUCION",
            stock_anterior=stock_ant,
            cantidad=detalle.cantidad,
            stock_nuevo=stock_nuevo,
            stock_defectuoso_anterior=stock_def_ant,
            stock_defectuoso_nuevo=stock_def_nuevo,
            observaciones=(
                f"Devolución {devolucion.id}"
            ),
            usuario=usuario,
        )

        variante.stock = stock_nuevo
        variante.stock_defectuoso = stock_def_nuevo

        variante.save(
            update_fields=[
                "stock",
                "stock_defectuoso",
                "fecha_actualizacion"
            ]
        )


def _venta_completamente_devuelta(venta):

    for detalle_venta in venta.detalles.all():

        devuelto = (
            DetalleDevolucion.objects
            .filter(
                detalle_venta=detalle_venta,
                devolucion__estado="APROBADA"
            )
            .aggregate(
                total=models.Sum("cantidad")
            )["total"]
            or 0
        )

        if devuelto < detalle_venta.cantidad:

            return False

    return True


# ============================================================
# CREAR DEVOLUCIÓN
# ============================================================

@transaction.atomic
def crear_devolucion(
    data,
    usuario
):

    venta = _validar_venta_devolucion(
        data["venta_id"],
        usuario
    )

    _validar_plazo(
        venta,
        data["tipo"]
    )

    # ========================================================
    # MÉTODO DE REEMBOLSO AUTOMÁTICO
    # ========================================================

    metodo_pago_reembolso = venta.metodo_pago

    if not metodo_pago_reembolso:

        raise BusinessException(
            "La venta no tiene un método de pago asociado."
        )

    factor_reembolso = (
        _calcular_factor_reembolso(
            venta
        )
    )

    devolucion = Devolucion.objects.create(
        venta=venta,
        usuario=usuario,
        metodo_pago_reembolso=metodo_pago_reembolso,
        tipo=data["tipo"],
        motivo=data["motivo"],
        estado="PENDIENTE",
    )

    total = _crear_detalles_devolucion(
        devolucion,
        venta,
        data["productos"],
        factor_reembolso
    )

    devolucion.total_devuelto = (
        _calcular_total_devuelto(
            venta,
            total
        )
    )

    devolucion.save(
        update_fields=[
            "total_devuelto"
        ]
    )

    registrar_bitacora(
        usuario=usuario,
        modulo="Devoluciones",
        accion="DEVOLUCION_CREADA",
        descripcion=(
            f"Devolución '{devolucion.id}' creada "
            f"para la venta '{venta.folio}' por "
            f"{usuario.nombre} {usuario.apellido}. "
            f"Tipo: {devolucion.tipo}. "
            f"Motivo: {devolucion.motivo}. "
            f"Total devuelto: "
            f"${devolucion.total_devuelto:.2f}. "
            f"Método de reembolso: "
            f"{metodo_pago_reembolso.nombre}. "
            f"Estado: PENDIENTE."
        ),
    )

    return devolucion


# ============================================================
# APROBAR DEVOLUCIÓN
# ============================================================

@transaction.atomic
def aprobar_devolucion(
    devolucion_id,
    usuario
):
    # ========================================================
    # OBTENER DEVOLUCIÓN SIN BLOQUEAR
    # ========================================================
    #
    # Solo necesitamos conocer la venta asociada para poder
    # adquirir los locks en el orden global correcto.
    #
    try:
        devolucion_base = (
            Devolucion.objects
            .get(id=devolucion_id)
        )

    except Devolucion.DoesNotExist:
        raise BusinessException(
            "La devolución no existe."
        )

    # ========================================================
    # OBTENER VENTA SIN BLOQUEAR
    # ========================================================

    try:
        venta_base = (
            Venta.objects
            .select_related("corte_caja")
            .get(id=devolucion_base.venta_id)
        )

    except Venta.DoesNotExist:
        raise BusinessException(
            "La venta asociada no existe."
        )

    if not venta_base.corte_caja:
        raise BusinessException(
            "La venta no tiene un corte de caja asociado."
        )

    caja_id = venta_base.corte_caja.caja_id
    corte_id = venta_base.corte_caja_id

    # ========================================================
    # LOCK 1: CAJA
    # ========================================================

    try:
        caja = (
            Caja.objects
            .select_for_update()
            .get(id=caja_id)
        )

    except Caja.DoesNotExist:
        raise BusinessException(
            "La caja asociada a la venta no existe."
        )

    # ========================================================
    # LOCK 2: CORTE
    # ========================================================

    try:
        corte = (
            CorteCaja.objects
            .select_for_update()
            .get(
                id=corte_id,
                caja=caja
            )
        )

    except CorteCaja.DoesNotExist:
        raise BusinessException(
            "El corte de caja asociado a la venta no existe."
        )

    # ========================================================
    # LOCK 3: VENTA
    # ========================================================

    try:
        venta = (
            Venta.objects
            .select_for_update()
            .get(id=devolucion_base.venta_id)
        )

    except Venta.DoesNotExist:
        raise BusinessException(
            "La venta asociada no existe."
        )

    # ========================================================
    # LOCK 4: DEVOLUCIÓN
    # ========================================================

    try:
        devolucion = (
            Devolucion.objects
            .select_for_update()
            .get(id=devolucion_id)
        )

    except Devolucion.DoesNotExist:
        raise BusinessException(
            "La devolución no existe."
        )

    # ========================================================
    # VALIDACIONES
    # ========================================================

    if devolucion.estado != "PENDIENTE":
        raise BusinessException(
            "Solo se pueden aprobar devoluciones pendientes."
        )

    if venta.estado == "CANCELADA":
        raise BusinessException(
            "No se puede aprobar una devolución "
            "de una venta cancelada."
        )

    if venta.estado == "DEVUELTA":
        raise BusinessException(
            "La venta ya fue devuelta completamente."
        )

    if not devolucion.metodo_pago_reembolso:
        raise BusinessException(
            "La devolución no tiene un método de reembolso."
        )

    metodo_pago = devolucion.metodo_pago_reembolso

    # ========================================================
    # LOCK 5: DETALLES DE VENTA
    # ========================================================
    #
    # Se bloquean los detalles involucrados antes de validar
    # cantidades para sincronizar devoluciones y garantías.
    #
    detalles_devolucion = list(
        devolucion.detalles.all()
    )

    if not detalles_devolucion:
        raise BusinessException(
            "La devolución no tiene productos."
        )

    detalle_venta_ids = sorted(
        {
            detalle.detalle_venta_id
            for detalle in detalles_devolucion
        },
        key=str
    )

    detalles_venta = list(
        DetalleVenta.objects
        .select_for_update()
        .filter(
            id__in=detalle_venta_ids,
            venta=venta
        )
        .order_by("id")
    )

    if len(detalles_venta) != len(detalle_venta_ids):
        raise BusinessException(
            "Uno o más productos de la devolución "
            "no pertenecen a la venta."
        )

    detalles_venta_map = {
        detalle.id: detalle
        for detalle in detalles_venta
    }

    # Reasociamos cada detalle de devolución con el
    # DetailVenta ya bloqueado.
    for detalle in detalles_devolucion:
        detalle.detalle_venta = detalles_venta_map[
            detalle.detalle_venta_id
        ]

    # ========================================================
    # VALIDAR CANTIDADES
    # ========================================================

    _validar_cantidades_aprobacion(
        detalles_devolucion,
        devolucion
    )

    # ========================================================
    # DETERMINAR CORTE PARA EL REEMBOLSO
    # ========================================================

    if metodo_pago.nombre == "EFECTIVO":
        corte = _obtener_corte_efectivo(
            caja,
            corte
        )

    # Para métodos no efectivos se conserva el corte de la
    # venta. El corte ya está bloqueado arriba para evitar
    # carreras con el cierre de caja.
    else:
        if corte is None:
            raise BusinessException(
                "La venta no tiene un corte de caja asociado."
            )

    # ========================================================
    # LOCK 6: VARIANTES
    # ========================================================
    #
    # _reponer_stock() adquiere los locks de las variantes.
    # Los detalles están ordenados por id, por lo que el
    # orden de adquisición queda determinístico.
    #
    # ========================================================

    _reponer_stock(
        detalles_devolucion,
        devolucion,
        usuario
    )

    # ========================================================
    # MOVIMIENTO DE CAJA
    # ========================================================

    MovimientoCaja.objects.create(
        corte_caja=corte,
        metodo_pago=metodo_pago,
        tipo="REEMBOLSO",
        monto=devolucion.total_devuelto,
        devolucion=devolucion,
        observaciones=(
            f"Reembolso de devolución "
            f"{devolucion.id}"
        ),
        usuario=usuario,
    )

    # ========================================================
    # ACTUALIZAR DEVOLUCIÓN
    # ========================================================

    devolucion.estado = "APROBADA"

    devolucion.save(
        update_fields=[
            "estado"
        ]
    )

    # ========================================================
    # BITÁCORA
    # ========================================================

    registrar_bitacora(
        usuario=usuario,
        modulo="Devoluciones",
        accion="DEVOLUCION_APROBADA",
        descripcion=(
            f"Devolución '{devolucion.id}' "
            f"aprobada por "
            f"{usuario.nombre} "
            f"{usuario.apellido}. "
            f"Venta: '{venta.folio}'. "
            f"Total devuelto: "
            f"${devolucion.total_devuelto:.2f}. "
            f"Método de reembolso: "
            f"{metodo_pago.nombre}."
        ),
    )

    # ========================================================
    # MARCAR VENTA COMO DEVUELTA
    # ========================================================

    if _venta_completamente_devuelta(venta):
        venta.estado = "DEVUELTA"

        venta.save(
            update_fields=[
                "estado"
            ]
        )

    return devolucion

# ============================================================
# RECHAZAR DEVOLUCIÓN
# ============================================================

@transaction.atomic
def cambiar_estado_devolucion(
    devolucion_id,
    nuevo_estado,
    usuario
):

    try:

        devolucion = (
            Devolucion.objects
            .select_for_update()
            .get(id=devolucion_id)
        )

    except Devolucion.DoesNotExist:

        raise BusinessException(
            "La devolución no existe."
        )

    if devolucion.estado != "PENDIENTE":

        raise BusinessException(
            "Solo se pueden modificar devoluciones pendientes."
        )

    if nuevo_estado != "RECHAZADA":

        raise BusinessException(
            "Para aprobar una devolución debe "
            "utilizarse el proceso de aprobación."
        )

    devolucion.estado = "RECHAZADA"

    devolucion.save(
        update_fields=[
            "estado"
        ]
    )

    registrar_bitacora(
        usuario=usuario,
        modulo="Devoluciones",
        accion="DEVOLUCION_RECHAZADA",
        descripcion=(
            f"Devolución '{devolucion.id}' "
            f"rechazada por "
            f"{usuario.nombre} "
            f"{usuario.apellido}. "
            f"Venta: '{devolucion.venta.folio}'. "
            f"Motivo registrado: "
            f"{devolucion.motivo}."
        ),
    )

    return devolucion