from django.db import transaction

from bitacora.services import registrar_bitacora
from config.exceptions import BusinessException

from corte_caja.models import CorteCaja

from .models import Usuario


def validar_no_automodificacion(
    actor,
    objetivo,
    accion="modificarte"
):

    if objetivo.id == actor.id:

        raise BusinessException(
            f"No puedes {accion}"
        )


def validar_jerarquia(
    actor,
    objetivo
):

    """
    Admin (rol=1) no puede operar sobre admins ni superadmins.
    Superadmin (rol=0) no puede operar sobre otros superadmins.
    """

    if actor.rol == 1 and objetivo.rol in (0, 1):

        raise BusinessException(
            "No tienes permisos para operar sobre este usuario."
        )

    if actor.rol == 0 and objetivo.rol == 0:

        raise BusinessException(
            "No puedes operar sobre otro superadministrador."
        )


def crear_usuario(
    serializer,
    actor
):

    with transaction.atomic():

        usuario = serializer.save()

        registrar_bitacora(

            usuario=actor,

            modulo="Usuarios",

            accion="CREAR_USUARIO",

            descripcion=(

                f"Usuario '{usuario.usuario}' creado correctamente por "

                f"{actor.nombre} {actor.apellido}."

            ),

        )

    return usuario


def crear_admin(
    serializer,
    actor
):

    with transaction.atomic():

        usuario = serializer.save()

        registrar_bitacora(

            usuario=actor,

            modulo="Usuarios",

            accion="CREAR_ADMIN",

            descripcion=(

                f"Administrador '{usuario.usuario}' creado correctamente por "

                f"{actor.nombre} {actor.apellido}."

            ),

        )

    return usuario


def modificar_usuario(
    usuario,
    validated_data,
    actor
):

    with transaction.atomic():

        datos = validated_data.copy()

        password = datos.pop(
            "password",
            None
        )

        if password:

            usuario.set_password(
                password
            )

        for attr, value in datos.items():

            setattr(
                usuario,
                attr,
                value
            )

        usuario.save()

        registrar_bitacora(

            usuario=actor,

            modulo="Usuarios",

            accion="MODIFICAR_USUARIO",

            descripcion=(

                f"Usuario '{usuario.usuario}' modificado correctamente por "

                f"{actor.nombre} {actor.apellido}."

            ),

        )

    return usuario


def desactivar_usuario(
    usuario,
    actor
):

    with transaction.atomic():
        usuario = Usuario.objects.select_for_update().get(
            pk=usuario.pk
        )

        corte_abierto = (
            CorteCaja.objects
            .select_for_update()
            .filter(
                usuario=usuario,
                fecha_fin__isnull=True
            )
            .exists()
        )

        if corte_abierto:

            raise BusinessException(
                "No puedes desactivar un usuario que tiene un corte de caja abierto."
            )

        usuario.activo = False

        usuario.save(
            update_fields=[
                "activo",
                "fecha_actualizacion"
            ]
        )

        registrar_bitacora(

            usuario=actor,

            modulo="Usuarios",

            accion="DESACTIVAR_USUARIO",

            descripcion=(

                f"Usuario '{usuario.usuario}' desactivado correctamente por "

                f"{actor.nombre} {actor.apellido}."

            ),

        )

    return usuario




def activar_usuario(
    usuario,
    actor
):

    if usuario.activo:

        raise BusinessException(
            "El usuario ya está activo."
        )

    with transaction.atomic():

        usuario.activo = True

        usuario.save(

            update_fields=[
                "activo",
                "fecha_actualizacion"
            ]

        )

        registrar_bitacora(

            usuario=actor,
            modulo="Usuarios",
            accion="ACTIVAR_USUARIO",
            descripcion=(

                f"Usuario '{usuario.usuario}' activado correctamente por "

                f"{actor.nombre} {actor.apellido}."

            ),

        )

    return usuario