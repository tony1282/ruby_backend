import uuid

from django.db import IntegrityError
from django.db.models import F

from rest_framework import (
    viewsets,
    status
)

from rest_framework.response import Response

from rest_framework.permissions import (
    IsAuthenticated
)

from rest_framework.decorators import action

from rest_framework.pagination import PageNumberPagination

from .models import Variante
from .serializers import VarianteSerializer
from .services import (
    crear_variante,
    actualizar_variante,
    activar_variante,
    desactivar_variante,
)

from usuarios.permissions import IsAdmin

from config.exceptions import BusinessException


class VariantePagination(
    PageNumberPagination
):

    page_size = 50

    page_size_query_param = "page_size"

    max_page_size = 200


class VarianteViewSet(
    viewsets.ModelViewSet
):

    queryset = (
        Variante.objects
        .filter(activo=True)
        .select_related(
            "producto",
            "producto__categoria"
        )
    )

    serializer_class = VarianteSerializer

    pagination_class = VariantePagination

    # ----------------------------------------------------------
    # SIN DELETE
    # ----------------------------------------------------------

    http_method_names = [
        "get",
        "post",
        "put",
        "patch",
        "head",
        "options"
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

        producto_id = (
            self.request.query_params.get(
                "producto"
            )
        )

        if producto_id:

            try:
                uuid.UUID(producto_id)

            except ValueError:
                return Variante.objects.none()

        # ------------------------------------------------------
        # OPERACIONES QUE NECESITAN ENCONTRAR INACTIVAS
        # ------------------------------------------------------

        if self.action in [
            "update",
            "partial_update",
            "activar",
            "desactivar"
        ]:

            queryset = Variante.objects.all()

            if producto_id:
                queryset = queryset.filter(
                    producto_id=producto_id
                )

            return queryset.select_related(
                "producto",
                "producto__categoria"
            )

        # ------------------------------------------------------
        # DETALLE ADMIN
        # ------------------------------------------------------

        if (
            self.action == "retrieve"
            and es_admin
        ):

            return (
                Variante.objects
                .all()
                .select_related(
                    "producto",
                    "producto__categoria"
                )
            )

        # ------------------------------------------------------
        # LISTADO ADMIN
        # ------------------------------------------------------

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

                    queryset = (
                        Variante.objects.all()
                    )

                else:

                    queryset = (
                        Variante.objects.filter(
                            activo=activo_param.lower()
                            in ("true", "1")
                        )
                    )

                if producto_id:

                    queryset = queryset.filter(
                        producto_id=producto_id
                    )

                return (
                    queryset
                    .select_related(
                        "producto",
                        "producto__categoria"
                    )
                    .order_by(
                        "nombre",
                        "id"
                    )
                )

        # ------------------------------------------------------
        # CONSULTA NORMAL
        # ------------------------------------------------------

        queryset = (
            Variante.objects
            .filter(activo=True)
        )

        if producto_id:

            queryset = queryset.filter(
                producto_id=producto_id
            )

        return (
            queryset
            .select_related(
                "producto",
                "producto__categoria"
            )
            .order_by(
                "nombre",
                "id"
            )
        )

    # ==========================================================
    # PERMISOS
    # ==========================================================

    def get_permissions(self):

        if self.action in [
            "list",
            "retrieve",
            "buscar_por_codigo",
            "alertas_stock"
        ]:

            return [
                IsAuthenticated()
            ]

        return [
            IsAuthenticated(),
            IsAdmin()
        ]

    # ==========================================================
    # CREAR
    # ==========================================================

    def create(
        self,
        request,
        *args,
        **kwargs
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
                        "la variante."
                    ),
                    "data": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            variante = crear_variante(
                validated_data=(
                    serializer.validated_data
                ),
                usuario=request.user
            )

        except BusinessException as exc:

            return Response(
                {
                    "success": False,
                    "message": str(exc),
                    "data": None
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except IntegrityError:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Ya existe una variante con "
                        "este SKU o código de barras."
                    ),
                    "data": None
                },
                status=status.HTTP_409_CONFLICT
            )

        serializer.instance = variante

        return Response(
            {
                "success": True,
                "message": (
                    "Variante registrada "
                    "correctamente."
                ),
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    # ==========================================================
    # MODIFICAR
    # ==========================================================

    def update(
        self,
        request,
        *args,
        **kwargs
    ):

        partial = kwargs.pop(
            "partial",
            False
        )

        instancia = self.get_object()

        serializer = self.get_serializer(
            instancia,
            data=request.data,
            partial=partial
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "message": (
                        "No se pudo modificar "
                        "la variante."
                    ),
                    "data": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            variante = actualizar_variante(
                instancia=instancia,
                validated_data=(
                    serializer.validated_data
                ),
                usuario=request.user
            )

        except BusinessException as exc:

            return Response(
                {
                    "success": False,
                    "message": str(exc),
                    "data": None
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except IntegrityError:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Ya existe una variante con "
                        "este SKU o código de barras."
                    ),
                    "data": None
                },
                status=status.HTTP_409_CONFLICT
            )

        serializer.instance = variante

        return Response(
            {
                "success": True,
                "message": (
                    "Variante modificada "
                    "correctamente."
                ),
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    # ==========================================================
    # ALERTAS DE STOCK
    # ==========================================================

    @action(
        detail=False,
        methods=["get"],
        url_path="alertas-stock"
    )
    def alertas_stock(
        self,
        request
    ):

        variantes = (
            Variante.objects
            .filter(
                activo=True,
                stock__lte=F("stock_minimo")
            )
            .select_related(
                "producto"
            )
            .order_by(
                "stock",
                "producto__nombre",
                "nombre"
            )
        )

        data = []

        for variante in variantes:

            data.append(
                {
                    "id": str(variante.id),
                    "producto": (
                        variante.producto.nombre
                    ),
                    "variante": (
                        variante.nombre
                    ),
                    "codigo_barras": (
                        variante.codigo_barras
                    ),
                    "sku": (
                        variante.sku
                    ),
                    "stock": (
                        variante.stock
                    ),
                    "stock_minimo": (
                        variante.stock_minimo
                    ),
                    "estado": (
                        "AGOTADO"
                        if variante.stock == 0
                        else "BAJO"
                    ),
                }
            )

        return Response(
            {
                "success": True,
                "message": (
                    "Alertas de stock obtenidas "
                    "correctamente."
                ),
                "data": data,
                "total": len(data),
            },
            status=status.HTTP_200_OK
        )

    # ==========================================================
    # ACTIVAR
    # ==========================================================

    @action(
        detail=True,
        methods=["post"],
        url_path="activar"
    )
    def activar(
        self,
        request,
        pk=None
    ):

        try:

            variante = activar_variante(
                variante_id=pk,
                usuario=request.user
            )

        except Variante.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": (
                        "No existe la variante "
                        "solicitada."
                    ),
                    "data": None
                },
                status=status.HTTP_404_NOT_FOUND
            )

        except BusinessException as exc:

            return Response(
                {
                    "success": False,
                    "message": str(exc),
                    "data": None
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "success": True,
                "message": (
                    "Variante activada "
                    "correctamente."
                ),
                "data": VarianteSerializer(
                    variante
                ).data
            },
            status=status.HTTP_200_OK
        )

    # ==========================================================
    # DESACTIVAR
    # ==========================================================

    @action(
        detail=True,
        methods=["post"],
        url_path="desactivar"
    )
    def desactivar(
        self,
        request,
        pk=None
    ):

        try:

            variante = desactivar_variante(
                variante_id=pk,
                usuario=request.user
            )

        except Variante.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": (
                        "No existe la variante "
                        "solicitada."
                    ),
                    "data": None
                },
                status=status.HTTP_404_NOT_FOUND
            )

        except BusinessException as exc:

            return Response(
                {
                    "success": False,
                    "message": str(exc),
                    "data": None
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "success": True,
                "message": (
                    "Variante desactivada "
                    "correctamente."
                ),
                "data": None
            },
            status=status.HTTP_200_OK
        )

    # ==========================================================
    # BUSCAR POR CÓDIGO DE BARRAS
    # ==========================================================

    @action(
        detail=False,
        methods=["get"],
        url_path=r"codigo/(?P<codigo>[^/.]+)"
    )
    def buscar_por_codigo(
        self,
        request,
        codigo=None
    ):

        variante = (
            Variante.objects
            .filter(
                codigo_barras=codigo,
                activo=True
            )
            .select_related(
                "producto",
                "producto__categoria"
            )
            .first()
        )

        if variante is None:

            return Response(
                {
                    "success": False,
                    "message": (
                        "No existe una variante "
                        "con ese código."
                    ),
                    "data": None
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(
            variante
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Variante encontrada."
                ),
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )