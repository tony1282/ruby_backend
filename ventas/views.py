import logging

from django.db.models import Prefetch, Sum, IntegerField, Value
from django.db.models.functions import Coalesce

from rest_framework import mixins, viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination

from .models import Venta
from .serializers import VentaSerializer
from .services import crear_venta, cancelar_venta

from devoluciones.models import DetalleDevolucion
from detalle_venta.models import DetalleVenta
from garantias.models import Garantia

from config.exceptions import BusinessException


logger = logging.getLogger(__name__)


# ==============================================================
# PAGINACIÓN
# ==============================================================

class VentaPagination(PageNumberPagination):

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


# ==============================================================
# VALIDAR USUARIO ACTIVO
# ==============================================================

def _usuario_activo(user):

    if not user.activo:
        return Response(
            {
                "success": False,
                "message": "El usuario está inactivo.",
                "data": None,
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    return None


# ==============================================================
# EJECUTAR SERVICIO
# ==============================================================

def _ejecutar_servicio(
    fn,
    log_msg,
):

    try:

        return fn(), None

    except BusinessException as e:

        return None, Response(
            {
                "success": False,
                "message": str(e),
                "data": getattr(
                    e,
                    "data",
                    None,
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception:

        logger.exception(
            log_msg
        )

        return None, Response(
            {
                "success": False,
                "message": "Error interno del servidor.",
                "data": None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ==============================================================
# CONSTRUIR MAPAS DE DEVOLUCIONES Y GARANTÍAS
# ==============================================================

def _construir_mapas(
    detalle_ids,
):
    if not detalle_ids:
        return {}, {}

    devueltas_map = {
        str(r["detalle_venta_id"]): r["total"]
        for r in (
            DetalleDevolucion.objects
            .filter(
                detalle_venta_id__in=detalle_ids,
                devolucion__estado__in=[
                    "PENDIENTE",
                    "APROBADA",
                ],
            )
            .values(
                "detalle_venta_id"
            )
            .annotate(
                total=Coalesce(
                    Sum("cantidad"),
                    Value(
                        0,
                        output_field=IntegerField(),
                    ),
                )
            )
        )
    }

    garantias_map = {
        str(r["detalle_venta_id"]): r["total"]
        for r in (
            Garantia.objects
            .filter(
                detalle_venta_id__in=detalle_ids,
                estado__in=[
                    "PENDIENTE",
                    "APROBADA",
                    "FINALIZADA",
                ],
            )
            .values(
                "detalle_venta_id"
            )
            .annotate(
                total=Coalesce(
                    Sum("cantidad"),
                    Value(
                        0,
                        output_field=IntegerField(),
                    ),
                )
            )
        )
    }

    return (
        devueltas_map,
        garantias_map,
    )


# ==============================================================
# SERIALIZAR DETALLE
# ==============================================================

def _serializar_detalle(
    detalle,
    devueltas_map,
    garantias_map,
):

    cantidad_devuelta = (
        devueltas_map.get(
            str(detalle.id),
            0,
        )
    )

    cantidad_garantia = (
        garantias_map.get(
            str(detalle.id),
            0,
        )
    )

    cantidad_disponible = max(
        detalle.cantidad
        - cantidad_devuelta
        - cantidad_garantia,
        0,
    )

    return {
        "detalle_id": detalle.id,
        "producto": (
            detalle.variante
            .producto
            .nombre
        ),
        "variante": (
            detalle.variante
            .nombre
        ),
        "variante_id": (
            detalle.variante
            .id
        ),
        "cantidad": (
            detalle.cantidad
        ),
        "cantidad_disponible": (
            cantidad_disponible
        ),
        "precio_unitario": (
            detalle.precio_unitario
        ),
        "descuento": (
            detalle.descuento
        ),
        "subtotal": (
            detalle.subtotal
        ),
    }


# ==============================================================
# SERIALIZAR VENTA
# ==============================================================

def _serializar_venta(
    venta,
):

    return {
        "id": venta.id,
        "folio": venta.folio,
        "fecha": venta.fecha,
        "usuario": venta.usuario.nombre,
        "metodo_pago": (
            venta.metodo_pago.nombre
        ),
        "caja": (
            venta.corte_caja
            .caja
            .nombre
        ),
        "subtotal": venta.subtotal,
        "descuento": venta.descuento,
        "iva": venta.iva,
        "total": venta.total,
        "estado": venta.estado,
    }


# ==============================================================
# VIEWSET DE VENTAS
# ==============================================================

class VentaViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):

    queryset = Venta.objects.all()

    serializer_class = VentaSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = [
        "get",
        "post",
        "head",
        "options",
    ]

    pagination_class = VentaPagination
    
    lookup_value_regex = (
        "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-"
        "[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
        "[0-9a-fA-F]{12}"
    )


    # ==========================================================
    # CREAR VENTA
    # ==========================================================

    def create(
        self,
        request,
        *args,
        **kwargs,
    ):

        error = _usuario_activo(
            request.user
        )

        if error:
            return error

        venta, err = (
            _ejecutar_servicio(
                lambda: crear_venta(
                    request.data,
                    request.user,
                ),
                "Error inesperado en crear_venta",
            )
        )

        if err:
            return err

        return Response(
            {
                "success": True,
                "message": (
                    "Venta registrada correctamente."
                ),
                "data": {
                    "id": venta.id,
                    "folio": venta.folio,
                },
            },
            status=status.HTTP_201_CREATED,
        )

    # ==========================================================
    # LISTAR VENTAS
    # ==========================================================

    def list(
        self,
        request,
        *args,
        **kwargs,
    ):
        error = _usuario_activo(
            request.user
        )
        
        if error:
            return error

        ventas = (
            Venta.objects
            .select_related(
                "usuario",
                "metodo_pago",
                "corte_caja",
                "corte_caja__caja",
            )
        )

        # ------------------------------------------------------
        # EMPLEADO:
        # únicamente sus propias ventas.
        #
        # ADMIN / SUPERADMIN:
        # pueden consultar todas.
        # ------------------------------------------------------

        if request.user.rol not in (0, 1):

            ventas = ventas.filter(
                usuario=request.user
            )

        paginator = VentaPagination()

        pagina = paginator.paginate_queryset(
            ventas,
            request,
        )

        resultados = [
            _serializar_venta(
                venta
            )
            for venta in pagina
        ]

        # ------------------------------------------------------
        # RESPUESTA ESTANDARIZADA
        # ------------------------------------------------------

        return Response(
            {
                "success": True,
                "message": (
                    "Ventas consultadas correctamente."
                ),
                "data": {
                    "count": (
                        paginator
                        .page
                        .paginator
                        .count
                    ),
                    "next": (
                        paginator
                        .get_next_link()
                    ),
                    "previous": (
                        paginator
                        .get_previous_link()
                    ),
                    "results": resultados,
                },
            },
            status=status.HTTP_200_OK,
        )

    # ==========================================================
    # CONSULTAR VENTA
    # ==============================================================

    def retrieve(
        self,
        request,
        pk=None,
    ):
        error = _usuario_activo(
            request.user
        )
        
        if error:
            return error

        queryset = (
            Venta.objects
            .select_related(
                "usuario",
                "metodo_pago",
                "corte_caja",
                "corte_caja__caja",
            )
            .prefetch_related(
                Prefetch(
                    "detalles",
                    queryset=DetalleVenta.objects
                    .select_related(
                        "variante",
                        "variante__producto",
                    )
                )
            )
        )

        try:

            if request.user.rol in (0, 1):

                venta = queryset.get(
                    pk=pk,
                )

            else:

                venta = queryset.get(
                    pk=pk,
                    usuario=request.user,
                )

        except (
            Venta.DoesNotExist,
            ValueError,
            TypeError,
        ):

            return Response(
                {
                    "success": False,
                    "message": (
                        "La venta no existe."
                    ),
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # ------------------------------------------------------
        # DETALLES
        # ------------------------------------------------------

        detalles = list(
            venta.detalles.all()
        )

        detalle_ids = [
            detalle.id
            for detalle in detalles
        ]

        (
            devueltas_map,
            garantias_map,
        ) = _construir_mapas(
            detalle_ids
        )

        productos = [
            _serializar_detalle(
                detalle,
                devueltas_map,
                garantias_map,
            )
            for detalle in detalles
        ]

        data = {
            **_serializar_venta(
                venta
            ),
            "productos": productos,
        }

        return Response(
            {
                "success": True,
                "message": (
                    "Venta consultada correctamente."
                ),
                "data": data,
            },
            status=status.HTTP_200_OK,
        )

    # ==========================================================
    # CANCELAR VENTA
    # ==========================================================

    @action(
        detail=True,
        methods=["post"],
        url_path="cancelar",
    )
    def cancelar(
        self,
        request,
        pk=None,
    ):

        error = _usuario_activo(
            request.user
        )

        if error:
            return error

        _, err = (
            _ejecutar_servicio(
                lambda: cancelar_venta(
                    pk,
                    request.user,
                ),
                "Error inesperado en cancelar_venta",
            )
        )

        if err:
            return err

        return Response(
            {
                "success": True,
                "message": (
                    "Venta cancelada correctamente."
                ),
                "data": None,
            },
            status=status.HTTP_200_OK,
        )