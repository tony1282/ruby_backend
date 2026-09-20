from django.db import transaction

from .models import Empresa
from bitacora.services import registrar_bitacora


class EmpresaNoExiste(Exception):
    pass


class EmpresaYaExiste(Exception):
    pass


def obtener_empresa():

    empresa = Empresa.objects.first()

    if not empresa:
        raise EmpresaNoExiste(
            "No hay configuración de empresa registrada."
        )

    return empresa


@transaction.atomic
def crear_empresa(*, usuario, datos):

    if Empresa.objects.exists():
        raise EmpresaYaExiste(
            "Ya existe una configuración de empresa. Use PUT para actualizar."
        )

    empresa = Empresa.objects.create(
        **datos
    )

    registrar_bitacora(
        usuario=usuario,
        modulo="Empresa",
        accion="CREAR_EMPRESA",
        descripcion="Se creó la configuración de la empresa."
    )

    return empresa


@transaction.atomic
def actualizar_empresa(*, usuario, datos):

    empresa = obtener_empresa()

    for campo, valor in datos.items():
        setattr(
            empresa,
            campo,
            valor
        )

    empresa.save()

    registrar_bitacora(
        usuario=usuario,
        modulo="Empresa",
        accion="ACTUALIZAR_EMPRESA",
        descripcion="Se actualizó la configuración de la empresa."
    )

    return empresa