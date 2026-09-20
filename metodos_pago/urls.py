from django.urls import path

from .views import (
    MetodoPagoView,
    MetodoPagoActivoView,
    MetodoPagoActivarView,
    MetodoPagoDesactivarView,
)

urlpatterns = [
    path(
        "metodos-pago/",
        MetodoPagoView.as_view()
    ),

    path(
        "metodos-pago/activos/",
        MetodoPagoActivoView.as_view()
    ),

    path(
        "metodos-pago/<uuid:id>/activar/",
        MetodoPagoActivarView.as_view()
    ),

    path(
        "metodos-pago/<uuid:id>/desactivar/",
        MetodoPagoDesactivarView.as_view()
    ),
]