from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from .models import DetalleVenta
from .serializers import DetalleVentaSerializer


class DetalleVentaPagination(PageNumberPagination):

    page_size = 50
    max_page_size = 200


class DetalleVentaViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):

    queryset = DetalleVenta.objects.all()

    serializer_class = DetalleVentaSerializer

    permission_classes = [
        IsAuthenticated
    ]

    pagination_class = DetalleVentaPagination

    lookup_value_regex = (
        "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-"
        "[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
        "[0-9a-fA-F]{12}"
    )

    # -------------------------------------------------------------------------
    # Este módulo no debe manejar directamente la lógica de una venta.
    #
    # DetalleVenta pertenece a una Venta y sus datos se consultan desde:
    #
    #     GET /api/ventas/{id}/
    #
    # El ViewSet se conserva temporalmente mientras se termina la auditoría
    # del módulo Ventas y se confirma que ningún endpoint externo depende
    # de /detalle-venta/.
    #
    # Una vez confirmado, este ViewSet y sus rutas podrán eliminarse.
    # -------------------------------------------------------------------------

    def get_permissions(self):

        if self.action in ["list", "retrieve"]:
            permission_classes = [
                IsAuthenticated
            ]

            return [
                permission()
                for permission in permission_classes
            ]

        return [
            IsAuthenticated()
        ]

    def get_queryset(self):

        queryset = (
            DetalleVenta.objects
            .select_related(
                "venta",
                "variante",
                "variante__producto",
            )
        )

        # Administrador y superadministrador pueden consultar
        # los detalles de cualquier venta.
        if self.request.user.rol in (0, 1):
            return queryset

        # Los empleados solamente pueden consultar
        # detalles pertenecientes a sus propias ventas.
        return queryset.filter(
            venta__usuario=self.request.user
        )