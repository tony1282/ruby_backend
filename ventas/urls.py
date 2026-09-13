from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import VentaViewSet


router = DefaultRouter()


router.register(
    "ventas",
    VentaViewSet,
    basename="ventas",
)


urlpatterns = [
    path(
        "",
        include(router.urls),
    ),
]