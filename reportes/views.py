import uuid
from datetime import date

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework import status

from django.utils import timezone

from rest_framework.exceptions import NotFound

from usuarios.permissions import IsAdmin

from ventas.models import Venta
from inventario.models import MovimientoInventario
from garantias.models import Garantia
from devoluciones.models import Devolucion

from .services import (
    reporte_resumen_dia,
    reporte_ventas,
    reporte_productos,
    reporte_inventario,
    reporte_stock_bajo,
    reporte_cortes,
    reporte_devoluciones,
    reporte_garantias,
    reporte_movimientos,
)

from .serializers import (
    ReporteResumenDiaSerializer,
    ReporteVentaSerializer,
    ReporteProductoSerializer,
    ReporteInventarioSerializer,
    ReporteStockBajoSerializer,
    ReporteCorteSerializer,
    ReporteDevolucionSerializer,
    ReporteGarantiaSerializer,
    ReporteMovimientoSerializer,
)


# ============================================================
# PERMISOS
# ============================================================

PERMISSION_ADMIN = [
    IsAuthenticated,
    IsAdmin,
]

PERMISSION_EMPLEADO = [
    IsAuthenticated,
]


# ============================================================
# PAGINACIÓN
# ============================================================

class ReportePagination(PageNumberPagination):

    page_size = 50

    page_size_query_param = "page_size"

    max_page_size = 200

    def paginate_queryset(self, queryset, request, view=None):

        try:
            return super().paginate_queryset(
                queryset,
                request,
                view
            )

        except NotFound:

            raise NotFound(
                "La página solicitada no es válida."
            )


# ============================================================
# CLASE BASE
# ============================================================

class BaseReporteView(APIView):

    def _parsear_fecha(self, valor, nombre):
        """
        Convierte una fecha YYYY-MM-DD a date.

        Si no se proporciona fecha:
            retorna (None, None)

        Si es inválida:
            retorna (None, Response(...))
        """

        if not valor:
            return None, None

        try:
            return date.fromisoformat(valor), None

        except ValueError:
            return None, Response(
                {
                    "success": False,
                    "message": (
                        f"{nombre} no es una fecha válida "
                        "(formato YYYY-MM-DD)."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _validar_rango(self, fecha_inicio, fecha_fin):
        """
        Valida que fecha_inicio no sea posterior a fecha_fin.
        """

        if (
            fecha_inicio
            and fecha_fin
            and fecha_inicio > fecha_fin
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        "fecha_inicio no puede ser posterior "
                        "a fecha_fin."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return None

    def _parsear_rango(self, request):
        """
        Parsea:

            fecha_inicio
            fecha_fin

        Retorna:

            (fecha_inicio, fecha_fin, error_response)
        """

        fecha_inicio, error = self._parsear_fecha(
            request.query_params.get("fecha_inicio"),
            "fecha_inicio",
        )

        if error:
            return None, None, error

        fecha_fin, error = self._parsear_fecha(
            request.query_params.get("fecha_fin"),
            "fecha_fin",
        )

        if error:
            return None, None, error

        error = self._validar_rango(
            fecha_inicio,
            fecha_fin,
        )

        if error:
            return None, None, error

        return fecha_inicio, fecha_fin, None

    def _paginar(
        self,
        request,
        data,
        serializer_class,
    ):
        """
        Aplica paginación estándar a los reportes.
        """

        paginator = ReportePagination()

        pagina = paginator.paginate_queryset(
            data,
            request,
        )

        return paginator.get_paginated_response(
            serializer_class(
                pagina,
                many=True,
            ).data
        )


# ============================================================
# RESUMEN DEL DÍA
# ============================================================

class ReporteResumenDiaView(BaseReporteView):

    permission_classes = PERMISSION_EMPLEADO

    def get(self, request):

        fecha_raw = request.query_params.get("fecha")

        if not fecha_raw:
            fecha = timezone.localdate()

        else:
            fecha, error = self._parsear_fecha(
                fecha_raw,
                "fecha",
            )

            if error:
                return error

        data = reporte_resumen_dia(
            fecha=fecha,
            usuario_id=(
                request.user.id
                if request.user.rol == 2
                else None
            ),
        )

        return Response(
            {
                "success": True,
                "data": ReporteResumenDiaSerializer(
                    data
                ).data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# REPORTE DE VENTAS
# ============================================================

class ReporteVentasView(BaseReporteView):

    permission_classes = PERMISSION_ADMIN

    def get(self, request):

        fecha_inicio, fecha_fin, error = (
            self._parsear_rango(request)
        )

        if error:
            return error

        usuario_id = request.query_params.get(
            "usuario"
        )

        estado = request.query_params.get(
            "estado"
        )
        

        # ----------------------------------------------------
        # Validación UUID del usuario
        # ----------------------------------------------------

        if usuario_id:

            try:
                uuid.UUID(str(usuario_id))

            except (
                ValueError,
                TypeError,
                AttributeError,
            ):
                return Response(
                    {
                        "success": False,
                        "message": (
                            "usuario no es un "
                            "identificador válido."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # ----------------------------------------------------
        # Validación estado de venta
        # ----------------------------------------------------

        if estado:

            estados_validos = {
                valor
                for valor, _ in Venta.ESTADOS
            }

            if estado not in estados_validos:
                return Response(
                    {
                        "success": False,
                        "message": (
                            "El estado de venta "
                            "no es válido."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        data = reporte_ventas(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            usuario_id=usuario_id,
            estado=estado,
        )

        return self._paginar(
            request,
            data,
            ReporteVentaSerializer,
        )


# ============================================================
# PRODUCTOS MÁS VENDIDOS
# ============================================================

class ReporteProductosView(BaseReporteView):

    permission_classes = PERMISSION_ADMIN

    def get(self, request):

        fecha_inicio, fecha_fin, error = (
            self._parsear_rango(request)
        )

        if error:
            return error

        data = reporte_productos(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )

        return self._paginar(
            request,
            data,
            ReporteProductoSerializer,
        )


# ============================================================
# INVENTARIO
# ============================================================

class ReporteInventarioView(BaseReporteView):

    permission_classes = PERMISSION_EMPLEADO

    def get(self, request):

        data = reporte_inventario()

        return self._paginar(
            request,
            data,
            ReporteInventarioSerializer,
        )


# ============================================================
# STOCK BAJO
# ============================================================

class ReporteStockBajoView(BaseReporteView):

    permission_classes = PERMISSION_EMPLEADO

    def get(self, request):

        data = reporte_stock_bajo()

        return self._paginar(
            request,
            data,
            ReporteStockBajoSerializer,
        )


# ============================================================
# CORTES DE CAJA
# ============================================================

class ReporteCortesView(BaseReporteView):

    permission_classes = PERMISSION_ADMIN

    def get(self, request):

        fecha_inicio, fecha_fin, error = (
            self._parsear_rango(request)
        )

        if error:
            return error

        data = reporte_cortes(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )

        return self._paginar(
            request,
            data,
            ReporteCorteSerializer,
        )


# ============================================================
# DEVOLUCIONES
# ============================================================

class ReporteDevolucionesView(BaseReporteView):

    permission_classes = PERMISSION_ADMIN

    def get(self, request):

        fecha_inicio, fecha_fin, error = (
            self._parsear_rango(request)
        )

        if error:
            return error

        estado = request.query_params.get(
            "estado"
        )
        
        tipo = request.query_params.get(
            "tipo"
        )

        # ----------------------------------------------------
        # Validación estado de devolución
        # ----------------------------------------------------

        if estado:

            estados_validos = {
                valor
                for valor, _ in (
                    Devolucion
                    ._meta
                    .get_field("estado")
                    .choices
                )
            }

            if estado not in estados_validos:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "El estado de devolución "
                            "no es válido."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
                
        if tipo:
            tipos_validos = {
                valor
                for valor, _ in Devolucion.TIPO_CHOICES
            }

            if tipo not in tipos_validos:
                return Response(
                    {
                        "success": False,
                        "message": (
                            "El tipo de devolución "
                            "no es válido."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        data = reporte_devoluciones(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado=estado,
            tipo=tipo,
        )
        
        return self._paginar(
            request,
            data,
            ReporteDevolucionSerializer,
        )


# ============================================================
# GARANTÍAS
# ============================================================

class ReporteGarantiasView(BaseReporteView):

    permission_classes = PERMISSION_ADMIN

    def get(self, request):

        fecha_inicio, fecha_fin, error = (
            self._parsear_rango(request)
        )

        if error:
            return error

        estado = request.query_params.get(
            "estado"
        )
        
        resolucion = request.query_params.get(
            "resolucion"
        )

        # ----------------------------------------------------
        # Validación estado de garantía
        # ----------------------------------------------------

        if estado:

            estados_validos = {
                valor
                for valor, _ in (
                    Garantia
                    ._meta
                    .get_field("estado")
                    .choices
                )
            }

            if estado not in estados_validos:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "El estado de garantía "
                            "no es válido."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
                
                
                    # ----------------------------------------------------
        # Validación resolución de garantía
        # ----------------------------------------------------

        if resolucion:

            resoluciones_validas = {
                valor
                for valor, _ in Garantia.RESOLUCION_CHOICES
            }

            if resolucion not in resoluciones_validas:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "La resolución de garantía "
                            "no es válida."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        data = reporte_garantias(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado=estado,
            resolucion=resolucion,
)

        return self._paginar(
            request,
            data,
            ReporteGarantiaSerializer,
        )


# ============================================================
# MOVIMIENTOS DE INVENTARIO
# ============================================================

class ReporteMovimientosView(BaseReporteView):

    permission_classes = PERMISSION_ADMIN

    def get(self, request):

        fecha_inicio, fecha_fin, error = (
            self._parsear_rango(request)
        )

        if error:
            return error

        tipo = request.query_params.get(
            "tipo"
        )

        # ----------------------------------------------------
        # Validación tipo de movimiento
        # ----------------------------------------------------

        if tipo:

            tipos_validos = {
                valor
                for valor, _ in MovimientoInventario.TIPOS
            }

            if tipo not in tipos_validos:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "El tipo de movimiento "
                            "no es válido."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        data = reporte_movimientos(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tipo=tipo,
        )

        return self._paginar(
            request,
            data,
            ReporteMovimientoSerializer,
        )