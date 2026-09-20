from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from usuarios.permissions import IsAdmin

from config.exceptions import BusinessException

from .serializers import MetodoPagoSerializer
from .services import (
    listar_metodos_pago,
    listar_metodos_pago_activos,
    activar_metodo_pago,
    desactivar_metodo_pago,
)


class MetodoPagoView(APIView):

    permission_classes = [
        IsAuthenticated
    ]


    # GET /api/metodos-pago/
    # Lista todos los métodos

    def get(self, request):

        metodos = listar_metodos_pago()

        serializer = MetodoPagoSerializer(
            metodos,
            many=True
        )

        return Response(
            {
                "success": True,
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )


    # POST /api/metodos-pago/
    # Los métodos son fijos

    def post(self, request):

        if not request.user.is_authenticated:

            return Response(
                {
                    "success": False,
                    "message": "Autenticación requerida."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not request.user.rol == 1:

            return Response(
                {
                    "success": False,
                    "message": "No tienes permisos para realizar esta acción."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(
            {
                "success": False,
                "message": (
                    "Los métodos de pago son fijos "
                    "y no pueden crearse."
                )
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


class MetodoPagoActivarView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin
    ]


    # POST /api/metodos-pago/<id>/activar/

    def post(self, request, id):

        if request.data:

            return Response(
                {
                    "success": False,
                    "message": (
                        "No se permiten datos. "
                        "La activación se realiza mediante el endpoint."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            metodo = activar_metodo_pago(
                metodo_id=id,
                usuario=request.user
            )

        except BusinessException as e:

            return Response(
                {
                    "success": False,
                    "message": str(e),
                    "data": None
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = MetodoPagoSerializer(
            metodo
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Método de pago activado correctamente."
                ),
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )


class MetodoPagoDesactivarView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin
    ]


    # POST /api/metodos-pago/<id>/desactivar/

    def post(self, request, id):

        if request.data:

            return Response(
                {
                    "success": False,
                    "message": (
                        "No se permiten datos. "
                        "La desactivación se realiza mediante el endpoint."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            metodo = desactivar_metodo_pago(
                metodo_id=id,
                usuario=request.user
            )

        except BusinessException as e:

            return Response(
                {
                    "success": False,
                    "message": str(e),
                    "data": None
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = MetodoPagoSerializer(
            metodo
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Método de pago desactivado correctamente."
                ),
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )


class MetodoPagoActivoView(APIView):

    permission_classes = [
        IsAuthenticated
    ]


    # GET /api/metodos-pago/activos/

    def get(self, request):

        metodos = listar_metodos_pago_activos()

        data = [
            {
                "id": metodo.id,
                "nombre": metodo.nombre
            }

            for metodo in metodos
        ]

        return Response(
            {
                "success": True,
                "data": data
            },
            status=status.HTTP_200_OK
        )