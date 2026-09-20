import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from usuarios.permissions import IsAdmin
from config.exceptions import BusinessException

from bitacora.services import registrar_bitacora

from .models import Garantia
from .serializers import (
    CrearGarantiaSerializer,
    ActualizarGarantiaSerializer,
    AprobarGarantiaSerializer,
    RechazarGarantiaSerializer,
    FinalizarGarantiaSerializer,
    GarantiaSerializer,
)
from .services import (
    crear_garantia,
    actualizar_garantia,
    aprobar_garantia,
    rechazar_garantia,
    finalizar_garantia,
)


class GarantiaPagination(PageNumberPagination):

    page_size = 50

    max_page_size = 200


class GarantiaListCreateView(APIView):

    permission_classes = [IsAuthenticated]

    # GET /api/garantias/
    def get(self, request):

        if request.user.rol in (0, 1):
            garantias = Garantia.objects.select_related(
                "venta",
                "detalle_venta",
                "variante",
                "variante__producto",
                "usuario",
                "variante_nueva"
            ).all()

        else:
            garantias = Garantia.objects.select_related(
                "venta",
                "detalle_venta",
                "variante",
                "variante__producto",
                "usuario",
                "variante_nueva"
            ).filter(
                usuario=request.user
            )

        paginator = GarantiaPagination()

        pagina = paginator.paginate_queryset(
            garantias,
            request
        )

        serializer = GarantiaSerializer(
            pagina,
            many=True
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    # POST /api/garantias/
    def post(self, request):

        serializer = CrearGarantiaSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:

            garantia = crear_garantia(
                serializer.validated_data,
                request.user
            )

            return Response(
                {
                    "success": True,
                    "message": "Garantía registrada correctamente.",
                    "data": GarantiaSerializer(garantia).data
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
                "Error inesperado en crear_garantia"
            )

            return Response(
                {
                    "success": False,
                    "message": "Error interno del servidor.",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GarantiaDetailView(APIView):

    permission_classes = [IsAuthenticated]

    # GET /api/garantias/<id>/
    def get(self, request, id):

        try:

            queryset = Garantia.objects.select_related(
                "venta",
                "detalle_venta",
                "variante",
                "variante__producto",
                "usuario",
                "variante_nueva"
            )

            if request.user.rol in (0, 1):
                garantia = queryset.get(
                    id=id
                )

            else:
                garantia = queryset.get(
                    id=id,
                    usuario=request.user
                )

        except Garantia.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "La garantía no existe.",
                    "data": None
                },
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "success": True,
                "message": "Garantía obtenida correctamente.",
                "data": GarantiaSerializer(garantia).data
            },
            status=status.HTTP_200_OK
        )

    # PUT /api/garantias/<id>/
    def put(self, request, id):
        if not request.user.activo:
            return Response(
                {
                    "success": False,
                    "message": "El usuario no está activo.",
                    "data": None
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ActualizarGarantiaSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            garantia = actualizar_garantia(
                id,
                serializer.validated_data,
                request.user
            )

            return Response(
                {
                    "success": True,
                    "message": (
                        "Garantía actualizada correctamente."
                    ),
                    "data": GarantiaSerializer(
                        garantia
                    ).data
                },
                status=status.HTTP_200_OK
            )

        except BusinessException as e:
            if str(e) == "La garantía no existe.":
                codigo = status.HTTP_404_NOT_FOUND

            elif str(e) == (
                "No tienes permisos para modificar esta garantía."
            ):
                codigo = status.HTTP_403_FORBIDDEN

            else:
                codigo = status.HTTP_400_BAD_REQUEST

            return Response(
                {
                    "success": False,
                    "message": str(e),
                    "data": None
                },
                status=codigo
            )

        except Exception:
            logging.getLogger(__name__).exception(
                "Error inesperado en actualizar_garantia"
            )

            return Response(
                {
                    "success": False,
                    "message": "Error interno del servidor.",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        
class GarantiaAprobarView(APIView):

    permission_classes = [IsAdmin]

    # POST /api/garantias/<id>/aprobar/
    def post(self, request, id):

        serializer = AprobarGarantiaSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:

            garantia = aprobar_garantia(
                id,
                serializer.validated_data,
                request.user
            )

            return Response(
                {
                    "success": True,
                    "message": (
                        "Garantía aprobada correctamente."
                    ),
                    "data": GarantiaSerializer(
                        garantia
                    ).data
                },
                status=status.HTTP_200_OK
            )

        except BusinessException as e:
            if str(e) == "La garantía no existe.":
                codigo = status.HTTP_404_NOT_FOUND
            else:
                codigo = status.HTTP_400_BAD_REQUEST
            
            return Response(
                {
                    "success": False,
                    "message": str(e),
                    "data": None
                },
                status=codigo
            )
        
        except Exception:

            logging.getLogger(__name__).exception(
                "Error inesperado en aprobar_garantia"
            )

            return Response(
                {
                    "success": False,
                    "message": "Error interno del servidor.",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GarantiaRechazarView(APIView):

    permission_classes = [IsAdmin]

    # POST /api/garantias/<id>/rechazar/
    def post(self, request, id):

        serializer = RechazarGarantiaSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:

            garantia = rechazar_garantia(
                id,
                serializer.validated_data,
                request.user
            )

            return Response(
                {
                    "success": True,
                    "message": (
                        "Garantía rechazada correctamente."
                    ),
                    "data": GarantiaSerializer(
                        garantia
                    ).data
                },
                status=status.HTTP_200_OK
            )

        except BusinessException as e:
            if str(e) == "La garantía no existe.":
                codigo = status.HTTP_404_NOT_FOUND
            else:
                codigo = status.HTTP_400_BAD_REQUEST
            return Response(
                {
                    "success": False,
                    "message": str(e),
                    "data": None
                },
                status=codigo
            ) 

        except Exception:

            logging.getLogger(__name__).exception(
                "Error inesperado en rechazar_garantia"
            )

            return Response(
                {
                    "success": False,
                    "message": "Error interno del servidor.",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GarantiaFinalizarView(APIView):

    permission_classes = [IsAdmin]

    # POST /api/garantias/<id>/finalizar/
    def post(self, request, id):

        serializer = FinalizarGarantiaSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:

            garantia = finalizar_garantia(
                id,
                serializer.validated_data,
                request.user
            )

            return Response(
                {
                    "success": True,
                    "message": (
                        "Garantía finalizada correctamente."
                    ),
                    "data": GarantiaSerializer(
                        garantia
                    ).data
                },
                status=status.HTTP_200_OK
            )

        except BusinessException as e:
            if str(e) == "La garantía no existe.":
                codigo = status.HTTP_404_NOT_FOUND
            else:
                codigo = status.HTTP_400_BAD_REQUEST
            return Response(
                {
                    "success": False,
                    "message": str(e),
                    "data": None
                },
                status=codigo
            )

        except Exception:

            logging.getLogger(__name__).exception(
                "Error inesperado en finalizar_garantia"
            )

            return Response(
                {
                    "success": False,
                    "message": "Error interno del servidor.",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )