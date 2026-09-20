from django.urls import path

from .views import (
    DevolucionListCreateView,
    DevolucionDetailView,
    DevolucionAprobarView,
    DevolucionRechazarView,
    VentaParaDevolucionView,
)


urlpatterns = [
    path(
        "devoluciones/",
        DevolucionListCreateView.as_view(),
        name="devoluciones-list-create",
    ),

    path(
        "devoluciones/ventas/<str:folio>/",
        VentaParaDevolucionView.as_view(),
        name="venta-para-devolucion",
    ),

    path(
        "devoluciones/<uuid:id>/",
        DevolucionDetailView.as_view(),
        name="devolucion-detail",
    ),

    path(
        "devoluciones/<uuid:id>/aprobar/",
        DevolucionAprobarView.as_view(),
        name="devolucion-aprobar",
    ),

    path(
        "devoluciones/<uuid:id>/rechazar/",
        DevolucionRechazarView.as_view(),
        name="devolucion-rechazar",
    ),
]