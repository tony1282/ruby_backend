import uuid
from django.db import transaction

from productos.models import Producto
from categorias.models import Categoria

from bitacora.services import registrar_bitacora
from config.exceptions import BusinessException


def _nombre_usuario(usuario):
    return (
        f"{usuario.nombre} {usuario.apellido}"
    ).strip()


# ==============================================================
# VALIDACIONES
# ==============================================================

def _obtener_categoria_bloqueada(pk):
    try:
        return (
            Categoria.objects
            .select_for_update()
            .get(pk=pk)
        )
    except Categoria.DoesNotExist:
        raise BusinessException(
            "La categoría asociada no existe."
        )


def _obtener_producto_bloqueado(pk):
    try:
        producto_uuid = uuid.UUID(str(pk))
    except (ValueError, TypeError, AttributeError):
        raise BusinessException(
            "El identificador del producto no es válido."
        )

    try:
        return (
            Producto.objects
            .select_for_update()
            .select_related("categoria")
            .get(pk=producto_uuid)
        )
    except Producto.DoesNotExist:
        raise BusinessException(
            "El producto solicitado no existe."
        )

def _validar_categoria_activa(categoria):
    if not categoria.activo:
        raise BusinessException(
            "No se puede utilizar una categoría inactiva."
        )


# ==============================================================
# CREAR PRODUCTO
# ==============================================================

@transaction.atomic
def crear_producto(
    *,
    validated_data,
    usuario,
):
    categoria = _obtener_categoria_bloqueada(
        validated_data["categoria"].pk
    )

    _validar_categoria_activa(categoria)

    validated_data["categoria"] = categoria

    producto = Producto.objects.create(
        **validated_data
    )

    registrar_bitacora(
        usuario=usuario,
        modulo="Productos",
        accion="CREAR_PRODUCTO",
        descripcion=(
            f"Producto '{producto.nombre}' creado "
            f"correctamente por "
            f"{_nombre_usuario(usuario)}."
        ),
    )

    return producto


# ==============================================================
# ACTUALIZAR PRODUCTO
# ==============================================================

@transaction.atomic
def actualizar_producto(
    *,
    instancia,
    validated_data,
    usuario,
):
    producto = _obtener_producto_bloqueado(
        instancia.pk
    )

    if "categoria" in validated_data:

        categoria = _obtener_categoria_bloqueada(
            validated_data["categoria"].pk
        )

        _validar_categoria_activa(categoria)

        validated_data["categoria"] = categoria

    for campo, valor in validated_data.items():
        setattr(
            producto,
            campo,
            valor,
        )

    producto.save()

    registrar_bitacora(
        usuario=usuario,
        modulo="Productos",
        accion="MODIFICAR_PRODUCTO",
        descripcion=(
            f"Producto '{producto.nombre}' "
            f"modificado correctamente por "
            f"{_nombre_usuario(usuario)}."
        ),
    )

    return producto


# ==============================================================
# ACTIVAR PRODUCTO
# ==============================================================

@transaction.atomic
def activar_producto(
    *,
    producto_id,
    usuario,
):
    producto = _obtener_producto_bloqueado(
        producto_id
    )

    if producto.activo:
        raise BusinessException(
            "El producto ya está activo."
        )

    categoria = _obtener_categoria_bloqueada(
        producto.categoria_id
    )

    _validar_categoria_activa(categoria)

    producto.activo = True

    producto.save(
        update_fields=[
            "activo",
            "fecha_actualizacion",
        ]
    )

    registrar_bitacora(
        usuario=usuario,
        modulo="Productos",
        accion="ACTIVAR_PRODUCTO",
        descripcion=(
            f"Producto '{producto.nombre}' "
            f"activado correctamente por "
            f"{_nombre_usuario(usuario)}."
        ),
    )

    return producto


# ==============================================================
# DESACTIVAR PRODUCTO
# ==============================================================

@transaction.atomic
def desactivar_producto(
    *,
    producto_id,
    usuario,
):
    producto = _obtener_producto_bloqueado(
        producto_id
    )

    if not producto.activo:
        raise BusinessException(
            "El producto ya está inactivo."
        )

    # ----------------------------------------------------------
    # NO DESACTIVAR SI TIENE VARIANTES ACTIVAS
    # ----------------------------------------------------------

    if producto.variantes.filter(
        activo=True
    ).exists():

        raise BusinessException(
            "No se puede desactivar el producto "
            "porque tiene variantes activas."
        )

    producto.activo = False

    producto.save(
        update_fields=[
            "activo",
            "fecha_actualizacion",
        ]
    )

    registrar_bitacora(
        usuario=usuario,
        modulo="Productos",
        accion="DESACTIVAR_PRODUCTO",
        descripcion=(
            f"Producto '{producto.nombre}' "
            f"desactivado correctamente por "
            f"{_nombre_usuario(usuario)}."
        ),
    )

    return producto