import re


from rest_framework import serializers

from .models import Usuario

from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer
)

from rest_framework.exceptions import (
    AuthenticationFailed
)


class ValidacionesUsuarioMixin:

    def validate_password(
        self,
        value
    ):

        if len(value) < 8:

            raise serializers.ValidationError(
                "La contraseña debe tener al menos 8 caracteres."
            )

        if not re.search(r"[A-Z]", value):

            raise serializers.ValidationError(
                "La contraseña debe contener al menos una mayúscula."
            )

        if not re.search(r"[a-z]", value):

            raise serializers.ValidationError(
                "La contraseña debe contener al menos una minúscula."
            )

        if not re.search(r"\d", value):

            raise serializers.ValidationError(
                "La contraseña debe contener al menos un número."
            )

        caracteres_especiales = "!@#$%^&*()_+-=[]{};':\"\\|,.<>/?"

        if not any(
            c in caracteres_especiales
            for c in value
        ):

            raise serializers.ValidationError(
                "La contraseña debe contener al menos un carácter especial."
            )

        return value


    def validate_usuario(
        self,
        value
    ):

        value = value.strip().lower()

        if not value:

            raise serializers.ValidationError(
                "El nombre de usuario es obligatorio."
            )

        queryset = Usuario.objects.filter(
            usuario=value
        )

        if self.instance:

            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():

            raise serializers.ValidationError(
                "Este nombre de usuario ya está registrado."
            )

        return value


    def validate_email(
        self,
        value
    ):

        value = value.strip().lower()

        if not value:

            raise serializers.ValidationError(
                "El correo electrónico es obligatorio."
            )

        queryset = Usuario.objects.filter(
            email=value
        )

        if self.instance:

            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():

            raise serializers.ValidationError(
                "Este correo electrónico ya está registrado."
            )

        return value


class UsuarioReadSerializer(
    serializers.ModelSerializer
):

    rol_nombre = serializers.CharField(
        source="get_rol_display",
        read_only=True
    )

    class Meta:

        model = Usuario

        fields = [
            "id",
            "nombre",
            "apellido",
            "usuario",
            "email",
            "rol",
            "rol_nombre",
            "activo",
            "fecha_creacion",
            "fecha_actualizacion",
        ]


class UsuarioSerializer(
    ValidacionesUsuarioMixin,
    serializers.ModelSerializer
):

    usuario = serializers.CharField(
        max_length=50
    )

    email = serializers.EmailField(
        max_length=150,
        error_messages={
            "invalid": "El correo electrónico no es válido."
        }
    )

    class Meta:

        model = Usuario

        fields = [
            "nombre",
            "apellido",
            "usuario",
            "email",
            "password",
        ]

        extra_kwargs = {

            "password": {
                "write_only": True,
            }

        }


    def __init__(
        self,
        *args,
        **kwargs
    ):

        super().__init__(
            *args,
            **kwargs
        )

        if self.instance is not None:

            self.fields["password"].required = False


    def create(
        self,
        validated_data
    ):

        password = validated_data.pop(
            "password"
        )

        return Usuario.objects.create_user(

            password=password,

            rol=2,

            activo=True,

            **validated_data
        )


class CrearAdminSerializer(
    ValidacionesUsuarioMixin,
    serializers.ModelSerializer
):

    usuario = serializers.CharField(
        max_length=50
    )

    email = serializers.EmailField(
        max_length=150,
        error_messages={
            "invalid": "El correo electrónico no es válido."
        }
    )

    class Meta:

        model = Usuario

        fields = [
            "nombre",
            "apellido",
            "usuario",
            "email",
            "password",
        ]

        extra_kwargs = {

            "password": {
                "write_only": True,
            }

        }


    def create(
        self,
        validated_data
    ):

        password = validated_data.pop(
            "password"
        )

        return Usuario.objects.create_user(

            password=password,

            rol=1,

            activo=True,

            **validated_data
        )


class LoginSerializer(
    TokenObtainPairSerializer
):

    def validate(
        self,
        attrs
    ):

        usuario_raw = attrs.get(
            "usuario",
            ""
        ) or ""

        attrs["usuario"] = usuario_raw.strip().lower()

        try:

            data = super().validate(
                attrs
            )

        except AuthenticationFailed:

            raise AuthenticationFailed(
                "Usuario o contraseña incorrectos."
            )

        usuario = self.user

        if not usuario.activo:

            raise AuthenticationFailed(
                "Usuario o contraseña incorrectos."
            )

        return {

            "success": True,

            "message": (
                "Inicio de sesión correcto."
            ),

            "data": {

                "access": data["access"],

                "refresh": data["refresh"],

                "usuario": {

                    "id": str(usuario.id),

                    "nombre": usuario.nombre,

                    "apellido": usuario.apellido,

                    "usuario": usuario.usuario,

                    "rol": usuario.rol,

                    "activo": usuario.activo

                }

            }

        }


class RefreshSerializer(
    TokenRefreshSerializer
):

    def validate(
        self,
        attrs
    ):

        from rest_framework_simplejwt.tokens import RefreshToken as RT
        from rest_framework_simplejwt.settings import api_settings
        from rest_framework_simplejwt.exceptions import TokenError

        try:

            refresh_obj = RT(
                attrs["refresh"]
            )

        except TokenError as e:

            raise AuthenticationFailed(
                str(e)
            )

        user_id = refresh_obj.payload.get(
            api_settings.USER_ID_CLAIM
        )

        try:

            usuario = Usuario.objects.get(
                **{
                    api_settings.USER_ID_FIELD: user_id
                }
            )

        except Usuario.DoesNotExist:

            raise AuthenticationFailed(
                "Usuario no encontrado."
            )

        if not usuario.activo:

            raise AuthenticationFailed(
                "Este usuario está inactivo."
            )

        data = super().validate(
            attrs
        )

        response = {

            "success": True,

            "message": (
                "Token actualizado correctamente."
            ),

            "data": {

                "access": data["access"]

            }

        }

        if "refresh" in data:

            response["data"]["refresh"] = data["refresh"]

        return response