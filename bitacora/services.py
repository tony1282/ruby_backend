import logging

from django.db import transaction

from .models import Bitacora


logger = logging.getLogger(__name__)


def registrar_bitacora(
    usuario,
    modulo,
    accion,
    descripcion
):
    def _registrar():

        try:

            Bitacora.objects.create(
                usuario=usuario,
                modulo=modulo,
                accion=accion,
                descripcion=descripcion
            )

        except Exception:

            logger.exception(
                "Error al registrar bitácora. "
                "Modulo=%s, Accion=%s, Usuario=%s",
                modulo,
                accion,
                getattr(usuario, "id", None)
            )

    transaction.on_commit(_registrar)