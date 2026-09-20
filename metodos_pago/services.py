from django.db import transaction

from config.exceptions import BusinessException
from bitacora.services import registrar_bitacora

from .models import MetodoPago


def listar_metodos_pago():
    return MetodoPago.objects.all()


def listar_metodos_pago_activos():
    return MetodoPago.objects.filter(
        activo=True
    )


def obtener_metodo_pago(metodo_id):
    try:
        return MetodoPago.objects.get(
            id=metodo_id
        )
    except MetodoPago.DoesNotExist:
        raise BusinessException(
            "Método de pago no encontrado."
        )


@transaction.atomic
def activar_metodo_pago(
    metodo_id,
    usuario
):
    try:
        metodo = (
            MetodoPago.objects
            .select_for_update()
            .get(id=metodo_id)
        )
    except MetodoPago.DoesNotExist:
        raise BusinessException(
            "Método de pago no encontrado."
        )

    metodo.activo = True

    metodo.save(
        update_fields=[
            "activo",
            "fecha_actualizacion"
        ]
    )

    registrar_bitacora(
        usuario=usuario,
        modulo="METODOS_PAGO",
        accion="ACTIVAR",
        descripcion=(
            f"Se activó el método de pago "
            f"{metodo.nombre}."
        )
    )

    return metodo


@transaction.atomic
def desactivar_metodo_pago(
    metodo_id,
    usuario
):
    try:
        metodo = (
            MetodoPago.objects
            .select_for_update()
            .get(id=metodo_id)
        )
    except MetodoPago.DoesNotExist:
        raise BusinessException(
            "Método de pago no encontrado."
        )

    metodo.activo = False

    metodo.save(
        update_fields=[
            "activo",
            "fecha_actualizacion"
        ]
    )

    registrar_bitacora(
        usuario=usuario,
        modulo="METODOS_PAGO",
        accion="DESACTIVAR",
        descripcion=(
            f"Se desactivó el método de pago "
            f"{metodo.nombre}."
        )
    )

    return metodo