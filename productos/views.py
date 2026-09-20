from django.db import IntegrityError

from rest_framework import (
    viewsets,
    status,
)

from rest_framework.response import Response

from rest_framework.permissions import (
    IsAuthenticated,
)

from rest_framework.decorators import action

from rest_framework.pagination import PageNumberPagination

from .models import Producto

from .serializers import (
    ProductoSerializer,
)

from .services import (
    crear_producto,
    actualizar_producto,
    activar_producto,
    desactivar_producto,
)

from usuarios.permissions import (
    IsAdmin,
)

from config.exceptions import BusinessException


class ProductoPagination(
    PageNumberPagination
):

    page_size = 50

    page_size_query_param = "page_size"

    max_page_size = 200


class ProductoViewSet(
    viewsets.ModelViewSet
):

    queryset = (
        Producto.objects
        .filter(activo=True)
        .select_related("categoria")
    )

    serializer_class = ProductoSerializer

    pagination_class = ProductoPagination

    # ==========================================================
    # SIN DELETE
    # ==========================================================

    http_method_names = [
        "get",
        "post",
        "put",
        "patch",
        "head",
        "options",
    ]

    # ==========================================================
    # QUERYSET
    # ==========================================================

    def get_queryset(self):

        user = self.request.user

        es_admin = (
            user
            and user.is_authenticated
            and getattr(user, "activo", False)
            and user.rol in (0, 1)
        )

        if self.action in [
            "update",
            "partial_update",
            "activar",
            "desactivar",
        ]:

            return (
                Producto.objects
                .all()
                .select_related("categoria")
            )

        if (
            self.action == "retrieve"
            and es_admin
        ):

            return (
                Producto.objects
                .all()
                .select_related("categoria")
            )

        if (
            self.action == "list"
            and es_admin
        ):

            activo_param = (
                self.request.query_params.get(
                    "activo"
                )
            )

            if activo_param is not None:

                if activo_param.lower() == "todos":

                    return (
                        Producto.objects
                        .all()
                        .select_related("categoria")
                        .order_by(
                            "nombre",
                            "id",
                        )
                    )

                return (
                    Producto.objects
                    .filter(
                        activo=(
                            activo_param.lower()
                            in ("true", "1")
                        )
                    )
                    .select_related("categoria")
                    .order_by(
                        "nombre",
                        "id",
                    )
                )

        return (
            Producto.objects
            .filter(activo=True)
            .select_related("categoria")
            .order_by(
                "nombre",
                "id",
            )
        )

    # ==========================================================
    # PERMISOS
    # ==========================================================

    def get_permissions(self):
        if self.action in [
            "list",
            "retrieve",
            "create",
            "update",
            "partial_update",
        ]:
            return [
                IsAuthenticated(),
            ]

        if self.action in [
            "activar",
            "desactivar",
        ]:
            return [
                IsAuthenticated(),
                IsAdmin(),
            ]

        return [
            IsAuthenticated(),
        ]

    # ==========================================================
    # CREAR
    # ==========================================================

    def create(
        self,
        request,
        *args,
        **kwargs,
    ):

        serializer = self.get_serializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "message": (
                        "No se pudo registrar "
                        "el producto."
                    ),
                    "data": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            producto = crear_producto(
                validated_data=(
                    serializer.validated_data
                ),
                usuario=request.user,
            )

        except BusinessException as exc:

            return Response(
                {
                    "success": False,
                    "message": str(exc),
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except IntegrityError:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Ya existe un producto "
                        "con este nombre."
                    ),
                    "data": None,
                },
                status=status.HTTP_409_CONFLICT,
            )

        serializer.instance = producto

        return Response(
            {
                "success": True,
                "message": (
                    "Producto registrado "
                    "correctamente."
                ),
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    # ==========================================================
    # MODIFICAR
    # ==========================================================

    def update(
        self,
        request,
        *args,
        **kwargs,
    ):

        partial = kwargs.pop(
            "partial",
            False,
        )

        instancia = self.get_object()

        serializer = self.get_serializer(
            instancia,
            data=request.data,
            partial=partial,
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "message": (
                        "No se pudo modificar "
                        "el producto."
                    ),
                    "data": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            producto = actualizar_producto(
                instancia=instancia,
                validated_data=(
                    serializer.validated_data
                ),
                usuario=request.user,
            )

        except BusinessException as exc:

            return Response(
                {
                    "success": False,
                    "message": str(exc),
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except IntegrityError:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Ya existe un producto "
                        "con este nombre."
                    ),
                    "data": None,
                },
                status=status.HTTP_409_CONFLICT,
            )

        serializer.instance = producto

        return Response(
            {
                "success": True,
                "message": (
                    "Producto modificado "
                    "correctamente."
                ),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    # ==========================================================
    # ACTIVAR
    # ==========================================================

    @action(
        detail=True,
        methods=["post"],
        url_path="activar",
    )
    def activar(
        self,
        request,
        pk=None,
    ):

        try:

            producto = activar_producto(
                producto_id=pk,
                usuario=request.user,
            )


        except BusinessException as exc:

            return Response(
                {
                    "success": False,
                    "message": str(exc),
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": (
                    "Producto activado "
                    "correctamente."
                ),
                "data": ProductoSerializer(
                    producto
                ).data,
            },
            status=status.HTTP_200_OK,
        )

    # ==========================================================
    # DESACTIVAR
    # ==========================================================

    @action(
        detail=True,
        methods=["post"],
        url_path="desactivar",
    )
    def desactivar(
        self,
        request,
        pk=None,
    ):

        try:

            producto = desactivar_producto(
                producto_id=pk,
                usuario=request.user,
            )


        except BusinessException as exc:

            return Response(
                {
                    "success": False,
                    "message": str(exc),
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": (
                    "Producto desactivado "
                    "correctamente."
                ),
                "data": None,
            },
            status=status.HTTP_200_OK,
        )