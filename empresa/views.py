import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .serializers import EmpresaSerializer
from .services import (
    obtener_empresa,
    crear_empresa,
    actualizar_empresa,
    EmpresaNoExiste,
    EmpresaYaExiste,
)

from usuarios.permissions import IsAdmin


logger = logging.getLogger(__name__)


class EmpresaView(APIView):

    def get_permissions(self):

        if self.request.method == "GET":
            return [IsAuthenticated()]

        return [
            IsAuthenticated(),
            IsAdmin()
        ]

    def get(self, request):

        try:

            empresa = obtener_empresa()

        except EmpresaNoExiste as e:

            return Response(
                {
                    "success": False,
                    "message": str(e),
                    "data": None
                },
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "success": True,
                "message": "Configuración de empresa obtenida correctamente.",
                "data": EmpresaSerializer(empresa).data
            },
            status=status.HTTP_200_OK
        )

    def post(self, request):

        serializer = EmpresaSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "message": "Los datos de la empresa no son válidos.",
                    "data": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            empresa = crear_empresa(
                usuario=request.user,
                datos=serializer.validated_data
            )

        except EmpresaYaExiste as e:

            return Response(
                {
                    "success": False,
                    "message": str(e),
                    "data": None
                },
                status=status.HTTP_409_CONFLICT
            )

        except Exception:

            logger.exception(
                "Error al crear configuración de empresa."
            )

            return Response(
                {
                    "success": False,
                    "message": "Error interno del servidor.",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                "success": True,
                "message": "Empresa registrada correctamente.",
                "data": EmpresaSerializer(empresa).data
            },
            status=status.HTTP_201_CREATED
        )

    def put(self, request):

        serializer = EmpresaSerializer(
            data=request.data,
            partial=True
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "message": "Los datos de la empresa no son válidos.",
                    "data": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            empresa = actualizar_empresa(
                usuario=request.user,
                datos=serializer.validated_data
            )

        except EmpresaNoExiste as e:

            return Response(
                {
                    "success": False,
                    "message": str(e),
                    "data": None
                },
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception:

            logger.exception(
                "Error al actualizar configuración de empresa."
            )

            return Response(
                {
                    "success": False,
                    "message": "Error interno del servidor.",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                "success": True,
                "message": "Empresa actualizada correctamente.",
                "data": EmpresaSerializer(empresa).data
            },
            status=status.HTTP_200_OK
        )