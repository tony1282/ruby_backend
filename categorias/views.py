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

from usuarios.permissions import IsAdmin

from config.exceptions import BusinessException

from .models import Categoria

from .serializers import (
    CategoriaSerializer
)

from .services import (
    crear_categoria,
    actualizar_categoria,
    activar_categoria,
    desactivar_categoria,
)


class CategoriaViewSet(
    viewsets.ModelViewSet
):

    queryset = Categoria.objects.all()

    serializer_class = CategoriaSerializer

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

        # ------------------------------------------------------
        # ADMIN
        # Puede consultar categorías activas e inactivas.
        # ------------------------------------------------------

        if (
            self.request.user.is_authenticated
            and self.request.user.rol in (0, 1)
            and self.request.user.activo
        ):

            return Categoria.objects.all().order_by(
                "nombre",
                "id",
            )

        # ------------------------------------------------------
        # EMPLEADO
        # Solo categorías activas.
        # ------------------------------------------------------

        return Categoria.objects.filter(
            activo=True
        ).order_by(
            "nombre",
            "id",
        )

    # ==========================================================
    # PERMISOS
    # ==========================================================
    def get_permissions(self):

    # ------------------------------------------------------
    # EMPLEADO + ADMIN/SUPERADMIN
    # Pueden crear y editar categorías.
    # ------------------------------------------------------

        if self.action in [
            "create",
            "update",
            "partial_update",
        ]:
            return [
                IsAuthenticated(),
            ]

    # ------------------------------------------------------
    # SOLO ADMIN/SUPERADMIN
    # Pueden activar y desactivar categorías.
    # ------------------------------------------------------

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
    # CREAR CATEGORÍA
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
                        "la categoría."
                    ),
                    "data": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            categoria = crear_categoria(
                validated_data=serializer.validated_data,
                usuario=request.user,
            )

        except IntegrityError:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Ya existe una categoría "
                        "con este nombre."
                    ),
                    "data": None,
                },
                status=status.HTTP_409_CONFLICT,
            )

        serializer.instance = categoria

        return Response(
            {
                "success": True,
                "message": (
                    "Categoría registrada "
                    "correctamente."
                ),
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    # ==========================================================
    # ACTUALIZAR CATEGORÍA
    # ==========================================================

    def update(
        self,
        request,
        *args,
        **kwargs,
    ):

        categoria = self.get_object()

        serializer = self.get_serializer(
            categoria,
            data=request.data,
            partial=False,
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "message": (
                        "No se pudo actualizar "
                        "la categoría."
                    ),
                    "data": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            categoria = actualizar_categoria(
                categoria_id=categoria.id,
                validated_data=serializer.validated_data,
                usuario=request.user,
            )

        except IntegrityError:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Ya existe una categoría "
                        "con este nombre."
                    ),
                    "data": None,
                },
                status=status.HTTP_409_CONFLICT,
            )

        serializer.instance = categoria

        return Response(
            {
                "success": True,
                "message": (
                    "Categoría actualizada "
                    "correctamente."
                ),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    # ==========================================================
    # PATCH
    # ==========================================================

    def partial_update(
        self,
        request,
        *args,
        **kwargs,
    ):

        categoria = self.get_object()

        serializer = self.get_serializer(
            categoria,
            data=request.data,
            partial=True,
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "message": (
                        "No se pudo actualizar "
                        "la categoría."
                    ),
                    "data": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            categoria = actualizar_categoria(
                categoria_id=categoria.id,
                validated_data=serializer.validated_data,
                usuario=request.user,
            )

        except IntegrityError:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Ya existe una categoría "
                        "con este nombre."
                    ),
                    "data": None,
                },
                status=status.HTTP_409_CONFLICT,
            )

        serializer.instance = categoria

        return Response(
            {
                "success": True,
                "message": (
                    "Categoría actualizada "
                    "correctamente."
                ),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    # ==========================================================
    # ACTIVAR CATEGORÍA
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

            categoria = activar_categoria(
                categoria_id=pk,
                usuario=request.user,
            )

        except BusinessException as exc:

            return Response(
                {
                    "success": False,
                    "message": str(exc),
                    "data": exc.data,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": (
                    "Categoría activada "
                    "correctamente."
                ),
                "data": CategoriaSerializer(
                    categoria
                ).data,
            },
            status=status.HTTP_200_OK,
        )

    # ==========================================================
    # DESACTIVAR CATEGORÍA
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

            categoria = desactivar_categoria(
                categoria_id=pk,
                usuario=request.user,
            )

        except BusinessException as exc:

            return Response(
                {
                    "success": False,
                    "message": str(exc),
                    "data": exc.data,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": (
                    "Categoría desactivada "
                    "correctamente."
                ),
                "data": None,
            },
            status=status.HTTP_200_OK,
        )