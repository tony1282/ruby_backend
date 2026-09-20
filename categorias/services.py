from django.db import transaction

from config.exceptions import BusinessException

from bitacora.services import registrar_bitacora

from .models import Categoria

import uuid


def _obtener_categoria_bloqueada(categoria_id):
    try:
        categoria_uuid = uuid.UUID(str(categoria_id))
    except (ValueError, TypeError, AttributeError):
        raise BusinessException(
            "El identificador de la categoría no es válido."
        )

    try:
        return (
            Categoria.objects
            .select_for_update()
            .get(pk=categoria_uuid)
        )
    except Categoria.DoesNotExist:
        raise BusinessException(
            "La categoría solicitada no existe."
        )

def crear_categoria(
    validated_data,
    usuario,
):
    """
    Crea una categoría y registra la operación
    en bitácora dentro de la misma transacción.
    """

    with transaction.atomic():

        categoria = Categoria.objects.create(
            **validated_data
        )

        registrar_bitacora(
            usuario=usuario,
            modulo="Categorias",
            accion="CREAR_CATEGORIA",
            descripcion=(
                f"Categoría '{categoria.nombre}' "
                f"creada por "
                f"{usuario.nombre} "
                f"{usuario.apellido}. "
                f"Descripción: "
                f"{categoria.descripcion or 'Sin descripción'}."
            )
        )

        return categoria


def actualizar_categoria(
    categoria_id,
    validated_data,
    usuario,
):
    """
    Actualiza una categoría y registra la operación
    en bitácora dentro de la misma transacción.
    """

    with transaction.atomic():

        categoria = _obtener_categoria_bloqueada(
            categoria_id
        )

        for campo, valor in validated_data.items():
            setattr(categoria, campo, valor)

        categoria.save()

        registrar_bitacora(
            usuario=usuario,
            modulo="Categorias",
            accion="ACTUALIZAR_CATEGORIA",
            descripcion=(
                f"Categoría '{categoria.nombre}' "
                f"actualizada por "
                f"{usuario.nombre} "
                f"{usuario.apellido}. "
                f"Descripción: "
                f"{categoria.descripcion or 'Sin descripción'}."
            )
        )

        return categoria


def activar_categoria(
    categoria_id,
    usuario,
):
    """
    Activa una categoría inactiva.
    """

    with transaction.atomic():

        categoria = _obtener_categoria_bloqueada(
            categoria_id
        )

        if categoria.activo:

            raise BusinessException(
                "La categoría ya está activa."
            )

        categoria.activo = True

        categoria.save(
            update_fields=[
                "activo",
                "fecha_actualizacion",
            ]
        )

        registrar_bitacora(
            usuario=usuario,
            modulo="Categorias",
            accion="ACTIVAR_CATEGORIA",
            descripcion=(
                f"Categoría '{categoria.nombre}' "
                f"activada correctamente por "
                f"{usuario.nombre} "
                f"{usuario.apellido}."
            )
        )

        return categoria


def desactivar_categoria(
    categoria_id,
    usuario,
):
    """
    Desactiva una categoría únicamente cuando
    no existen productos activos asociados.
    """

    with transaction.atomic():

        categoria = _obtener_categoria_bloqueada(
            categoria_id
        )

        if not categoria.activo:

            raise BusinessException(
                "La categoría ya está inactiva."
            )

        if categoria.productos.filter(
            activo=True
        ).exists():

            raise BusinessException(
                "No se puede desactivar "
                "la categoría porque tiene "
                "productos activos."
            )

        categoria.activo = False

        categoria.save(
            update_fields=[
                "activo",
                "fecha_actualizacion",
            ]
        )

        registrar_bitacora(
            usuario=usuario,
            modulo="Categorias",
            accion="DESACTIVAR_CATEGORIA",
            descripcion=(
                f"Categoría '{categoria.nombre}' "
                f"desactivada correctamente por "
                f"{usuario.nombre} "
                f"{usuario.apellido}."
            )
        )

        return categoria