import uuid
from django.db import transaction

from variantes.models import Variante
from productos.models import Producto
from inventario.services import registrar_entrada
from bitacora.services import registrar_bitacora
from config.exceptions import BusinessException


def _nombre_usuario(usuario):
    return (
        f"{usuario.nombre} {usuario.apellido}"
    ).strip()


# ==============================================================
# VALIDACIONES
# ==============================================================

def _validar_producto_activo(producto):
    if not producto.activo:
        raise BusinessException(
            "No se puede asociar una variante a un producto inactivo."
        )

    if not producto.categoria.activo:
        raise BusinessException(
            "No se puede asociar una variante a un producto "
            "cuya categoría está inactiva."
        )


def _validar_precios(
    costo,
    precio_menudeo,
    precio_mayoreo,
):
    if precio_menudeo < costo:
        raise BusinessException(
            "El precio menudeo no puede ser menor al costo."
        )

    if precio_mayoreo < costo:
        raise BusinessException(
            "El precio mayoreo no puede ser menor al costo."
        )


def _normalizar_sku(sku):
    return sku.strip().upper()


def _validar_unicidad(
    *,
    producto=None,
    nombre=None,
    sku=None,
    codigo_barras=None,
    excluir_pk=None,
):
    queryset = Variante.objects.all()

    if excluir_pk is not None:
        queryset = queryset.exclude(pk=excluir_pk)

    if producto is not None and nombre is not None:
        if queryset.filter(
            producto_id=producto.pk,
            nombre=nombre,
        ).exists():
            raise BusinessException(
                "Ya existe una variante con este nombre para este producto."
            )

    if sku is not None and queryset.filter(
        sku__iexact=sku,
    ).exists():
        raise BusinessException(
            "Ya existe una variante con este SKU."
        )

    if (
        codigo_barras is not None
        and queryset.filter(
            codigo_barras=codigo_barras
        ).exists()
    ):
        raise BusinessException(
            "Ya existe una variante con este código de barras."
        )

def _obtener_producto_bloqueado(pk):
    try:
        return (
            Producto.objects
            .select_for_update()
            .select_related("categoria")
            .get(pk=pk)
        )
    except Producto.DoesNotExist:
        raise BusinessException(
            "El producto asociado no existe."
        )


def _obtener_variante_bloqueada(pk):
    try:
        variante_uuid = uuid.UUID(str(pk))
    except (ValueError, TypeError, AttributeError):
        raise BusinessException(
            "El identificador de la variante no es válido."
        )

    try:
        return (
            Variante.objects
            .select_for_update()
            .select_related(
                "producto",
                "producto__categoria",
            )
            .get(pk=variante_uuid)
        )
    except Variante.DoesNotExist:
        raise BusinessException(
            "La variante solicitada no existe."
        )
# ==============================================================
# CREAR VARIANTE
# ==============================================================

@transaction.atomic
def crear_variante(*, validated_data, usuario):

    producto = _obtener_producto_bloqueado(
        validated_data["producto"].pk
    )

    _validar_producto_activo(producto)

    validated_data["sku"] = _normalizar_sku(
        validated_data["sku"]
    )

    _validar_unicidad(
        producto=producto,
        nombre=validated_data["nombre"],
        sku=validated_data.get("sku"),
        codigo_barras=validated_data.get(
            "codigo_barras"
        ),
    )

    _validar_precios(
        costo=validated_data.get("costo", 0),
        precio_menudeo=validated_data.get(
            "precio_menudeo",
            0,
        ),
        precio_mayoreo=validated_data.get(
            "precio_mayoreo",
            0,
        ),
    )

    # ----------------------------------------------------------
    # El stock recibido desde el formulario representa STOCK
    # INICIAL.
    #
    # No lo guardamos directamente.
    #
    # Primero lo extraemos y la variante nace con stock = 0.
    # Después registrar_entrada() será quien genere el movimiento
    # y actualice el stock.
    # ----------------------------------------------------------

    stock_inicial = validated_data.pop(
        "stock",
        0,
    )

    validated_data["producto"] = producto
    validated_data["stock"] = 0

    variante = Variante.objects.create(
        **validated_data
    )

    # ----------------------------------------------------------
    # REGISTRAR STOCK INICIAL
    #
    # registrar_entrada() ya:
    #
    # - bloquea la variante;
    # - valida cantidad;
    # - crea MovimientoInventario;
    # - actualiza stock;
    # - registra Bitácora.
    #
    # Todo permanece dentro del transaction.atomic() exterior.
    # ----------------------------------------------------------

    if stock_inicial > 0:
        registrar_entrada(
            variante_id=variante.id,
            cantidad=stock_inicial,
            observaciones=(
                "Stock inicial de la variante."
            ),
            usuario=usuario,
        )

        # Refrescamos el objeto para que el serializer final
        # devuelva el stock actualizado.
        variante.refresh_from_db()

    registrar_bitacora(
        usuario=usuario,
        modulo="Variantes",
        accion="CREAR_VARIANTE",
        descripcion=(
            f"Variante '{variante.nombre}' del producto "
            f"'{producto.nombre}' creada correctamente por "
            f"{_nombre_usuario(usuario)}."
        ),
    )

    return variante


# ==============================================================
# ACTUALIZAR VARIANTE
# ==============================================================

@transaction.atomic
def actualizar_variante(
    *,
    instancia,
    validated_data,
    usuario,
):
    variante = _obtener_variante_bloqueada(
        instancia.pk
    )

    producto_actual = _obtener_producto_bloqueado(
        variante.producto_id
    )

    if "producto" in validated_data:
        raise BusinessException(
            "El producto de una variante no puede modificarse."
        )   

    if variante.activo:
        _validar_producto_activo(
            producto_actual
    )

    if "sku" in validated_data:
        validated_data["sku"] = _normalizar_sku(
            validated_data["sku"]
    )

    _validar_unicidad(
        producto=producto_actual,
        nombre=validated_data.get(
            "nombre",
            variante.nombre,
        ),
        
        sku=validated_data.get(
            "sku",
            variante.sku,
            ),
        codigo_barras=validated_data.get(
            "codigo_barras",
            variante.codigo_barras,
            ),
        excluir_pk=variante.pk,
    )

    _validar_precios(
        costo=validated_data.get(
            "costo",
            variante.costo,
        ),
        precio_menudeo=validated_data.get(
            "precio_menudeo",
            variante.precio_menudeo,
        ),
        precio_mayoreo=validated_data.get(
            "precio_mayoreo",
            variante.precio_mayoreo,
        ),
    )

    for campo, valor in validated_data.items():
        setattr(
            variante,
            campo,
            valor,
        )

    variante.save()

    registrar_bitacora(
        usuario=usuario,
        modulo="Variantes",
        accion="MODIFICAR_VARIANTE",
        descripcion=(
            f"Variante '{variante.nombre}' del producto "
            f"'{variante.producto.nombre}' modificada "
            f"correctamente por "
            f"{_nombre_usuario(usuario)}."
        ),
    )

    return variante


# ==============================================================
# ACTIVAR
# ==============================================================

@transaction.atomic
def activar_variante(
    *,
    variante_id,
    usuario,
):
    variante = _obtener_variante_bloqueada(
        variante_id
    )

    if variante.activo:
        raise BusinessException(
            "La variante ya está activa."
        )

    producto = _obtener_producto_bloqueado(
        variante.producto_id
    )

    _validar_producto_activo(producto)

    variante.activo = True

    variante.save(
        update_fields=[
            "activo",
            "fecha_actualizacion",
        ]
    )

    registrar_bitacora(
        usuario=usuario,
        modulo="Variantes",
        accion="ACTIVAR_VARIANTE",
        descripcion=(
            f"Variante '{variante.nombre}' del producto "
            f"'{variante.producto.nombre}' activada correctamente "
            f"por {_nombre_usuario(usuario)}."
        ),
    )

    return variante


# ==============================================================
# DESACTIVAR
# ==============================================================

@transaction.atomic
def desactivar_variante(
    *,
    variante_id,
    usuario,
):
    variante = _obtener_variante_bloqueada(
        variante_id
    )

    if not variante.activo:
        raise BusinessException(
            "La variante ya está inactiva."
        )

    variante.activo = False

    variante.save(
        update_fields=[
            "activo",
            "fecha_actualizacion",
        ]
    )

    registrar_bitacora(
        usuario=usuario,
        modulo="Variantes",
        accion="DESACTIVAR_VARIANTE",
        descripcion=(
            f"Variante '{variante.nombre}' del producto "
            f"'{variante.producto.nombre}' desactivada correctamente "
            f"por {_nombre_usuario(usuario)}."
        ),
    )

    return variante