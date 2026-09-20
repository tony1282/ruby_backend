import logging


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from config.pagination import StandardPagination
from config.exceptions import BusinessException


from .permissions import EsAdministrador

from .serializers import (
    DevolucionSerializer,
    CrearDevolucionSerializer,
    ActualizarDevolucionSerializer,
    VentaParaDevolucionSerializer,
)

from .services import (
    crear_devolucion,
    actualizar_devolucion,
    aprobar_devolucion,
    cambiar_estado_devolucion,
    obtener_venta_para_devolucion,
)

from .models import Devolucion


class DevolucionListCreateView(APIView):

    permission_classes = [
        IsAuthenticated
    ]


    # GET /api/devoluciones/

    def get(self, request):

        if request.user.rol in (0, 1):
            devoluciones = Devolucion.objects.all()
        else:
            devoluciones = Devolucion.objects.filter(
                usuario=request.user
            )
            
        devoluciones = (
            devoluciones.select_related(
                "venta",
                "usuario",
                "metodo_pago_reembolso"
            )
            .prefetch_related(
                "detalles__detalle_venta__variante__producto"
            )
            .order_by("-fecha")
        )

        paginator = StandardPagination()

        pagina = paginator.paginate_queryset(
            devoluciones,
            request
        )

        serializer = DevolucionSerializer(
            pagina,
            many=True
        )

        return paginator.get_paginated_response(
            serializer.data
        )


    # POST /api/devoluciones/

    def post(self, request):

        serializer = CrearDevolucionSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:

            devolucion = crear_devolucion(
                serializer.validated_data,
                request.user
            )

            response = DevolucionSerializer(
                devolucion
            )

            return Response(
                {
                    "success": True,
                    "message": (
                        "Devolución registrada correctamente."
                    ),
                    "data": response.data
                },
                status=status.HTTP_201_CREATED
            )

        except BusinessException as e:

            return Response(
                {
                    "success": False,
                    "message": str(e),
                    "data": None
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception:

            logging.getLogger(__name__).exception(
                "Error inesperado en crear_devolucion"
            )

            return Response(
                {
                    "success": False,
                    "message": "Error interno del servidor.",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DevolucionDetailView(APIView):

    permission_classes = [
        IsAuthenticated
    ]


    # GET /api/devoluciones/{id}/

    def get(
        self,
        request,
        id
    ):

        try:
            
            queryset = Devolucion.objects.select_related(
                "venta",
                "usuario",
                "metodo_pago_reembolso"
            ).prefetch_related(
                "detalles__detalle_venta__variante__producto"
            )

            if request.user.rol in (0,1):
                devolucion = queryset.get(
                    id=id
                )
            else:
                devolucion = queryset.get(
                    id=id,
                    usuario=request.user
                )

        except Devolucion.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": (
                        "La devolución no existe."
                    ),
                    "data": None
                },
                status=status.HTTP_404_NOT_FOUND
            )


        serializer = DevolucionSerializer(
            devolucion
        )

        return Response(
            {
                "success": True,
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )


    # PUT /api/devoluciones/{id}/

    def put(
            self,
            request,
            id
        ):

        serializer = ActualizarDevolucionSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            devolucion = actualizar_devolucion(
                id,
                serializer.validated_data,
                request.user
            )

            response = DevolucionSerializer(
                devolucion
            )

            return Response(
                {
                    "success": True,
                    "message": (
                        "Devolución actualizada correctamente."
                    ),
                    "data": response.data
                },
                status=status.HTTP_200_OK
            )

        except BusinessException as e:
            return Response(
                {
                    "success": False,
                    "message": str(e),
                    "data": None
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception:
            logging.getLogger(__name__).exception(
                "Error inesperado en actualizar_devolucion"
            )

            return Response(
                {
                    "success": False,
                    "message": (
                        "Error interno del servidor."
                    ),
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DevolucionAprobarView(APIView):

    permission_classes = [
        IsAuthenticated,
        EsAdministrador
    ]


    # POST /api/devoluciones/{id}/aprobar/

    def post(
        self,
        request,
        id
    ):

        try:

            devolucion = aprobar_devolucion(
                id,
                request.user
            )

            serializer = DevolucionSerializer(
                devolucion
            )

            return Response(
                {
                    "success": True,
                    "message": (
                        "Devolución aprobada correctamente."
                    ),
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )

        except BusinessException as e:

            return Response(
                {
                    "success": False,
                    "message": str(e),
                    "data": None
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception:

            logging.getLogger(__name__).exception(
                "Error inesperado en aprobar_devolucion"
            )

            return Response(
                {
                    "success": False,
                    "message": "Error interno del servidor.",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DevolucionRechazarView(APIView):

    permission_classes = [
        IsAuthenticated,
        EsAdministrador
    ]


    # POST /api/devoluciones/{id}/rechazar/

    def post(
        self,
        request,
        id
    ):

        try:

            devolucion = cambiar_estado_devolucion(
                id,
                "RECHAZADA",
                request.user
            )

            serializer = DevolucionSerializer(
                devolucion
            )

            return Response(
                {
                    "success": True,
                    "message": (
                        "Devolución rechazada correctamente."
                    ),
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )

        except BusinessException as e:

            return Response(
                {
                    "success": False,
                    "message": str(e),
                    "data": None
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception:

            logging.getLogger(__name__).exception(
                "Error inesperado en cambiar_estado_devolucion"
            )

            return Response(
                {
                    "success": False,
                    "message": "Error interno del servidor.",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
class VentaParaDevolucionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, folio):
        try:
            data = obtener_venta_para_devolucion(
                folio=folio,
                usuario=request.user,
            )

            serializer = VentaParaDevolucionSerializer(data)

            return Response({
                "success": True,
                "message": "Venta consultada correctamente.",
                "data": serializer.data,
            }, status=status.HTTP_200_OK)

        except BusinessException as e:
            return Response({
                "success": False,
                "message": str(e),
                "data": None,
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            logging.getLogger(__name__).exception(
                "Error inesperado en obtener_venta_para_devolucion"
                )
            
            return Response({
                "success": False,
                "message": "Error interno del servidor.",
                "data": None,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)