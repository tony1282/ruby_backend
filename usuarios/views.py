from uuid import UUID

from django.db import IntegrityError

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

from .throttles import LoginRateThrottle

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import Usuario

from .serializers import (
    UsuarioSerializer,
    UsuarioReadSerializer,
    CrearAdminSerializer,
    LoginSerializer,
    RefreshSerializer
)

from .permissions import (
    IsAdmin,
    IsSuperAdmin
)

from .services import (
    crear_usuario,
    crear_admin,
    modificar_usuario,
    desactivar_usuario,
    activar_usuario,
    validar_no_automodificacion,
    validar_jerarquia
)

from config.exceptions import BusinessException

from rest_framework.exceptions import (
    ValidationError,
    NotFound
)


class UsuarioViewSet(viewsets.ModelViewSet):

    queryset = Usuario.objects.none()

    serializer_class = UsuarioSerializer

    permission_classes = [
        IsAuthenticated,
        IsAdmin
    ]

    http_method_names = [
        "get",
        "post",
        "put",
        "head",
        "options"
    ]

    def get_queryset(self):

        user = self.request.user

        if user.rol == 1:

            if self.action in (
                "list",
                "retrieve"
            ):

                return Usuario.objects.filter(
                    rol=2
                )

            return Usuario.objects.filter(
                rol__in=(1, 2)
            )

        return Usuario.objects.all()

    def get_object(self):

        pk = self.kwargs.get(
            self.lookup_field
        )

        try:

            UUID(str(pk))

        except (
            ValueError,
            TypeError,
            AttributeError
        ):

            raise ValidationError({
                "id": "El ID debe ser un UUID válido."
            })

        try:
            
            return super().get_object()
        
        except NotFound:
            raise BusinessException(
                "Usuario no encontrado."
            )


    def get_serializer_class(self):

        if self.action in (
            "list",
            "retrieve"
        ):

            return UsuarioReadSerializer

        return UsuarioSerializer

    def create(
        self,
        request,
        *args,
        **kwargs
    ):

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:

            usuario = crear_usuario(
                serializer,
                request.user
            )

        except IntegrityError:

            raise BusinessException(
                "El usuario o correo ya existe."
            )

        return Response(
            {
                "success": True,
                "message": "Usuario creado correctamente.",
                "data": UsuarioReadSerializer(
                    usuario
                ).data
            },
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[
            IsAuthenticated,
            IsSuperAdmin
        ]
    )
    def crear_admin(
        self,
        request,
        *args,
        **kwargs
    ):

        serializer = CrearAdminSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:

            usuario = crear_admin(
                serializer,
                request.user
            )

        except IntegrityError:

            raise BusinessException(
                "El usuario o correo ya existe."
            )

        return Response(
            {
                "success": True,
                "message": "Administrador creado correctamente.",
                "data": UsuarioReadSerializer(
                    usuario
                ).data
            },
            status=status.HTTP_201_CREATED
        )

    def update(
        self,
        request,
        *args,
        **kwargs
    ):

        usuario = self.get_object()

        validar_no_automodificacion(
            request.user,
            usuario
        )

        validar_jerarquia(
            request.user,
            usuario
        )

        serializer = self.get_serializer(
            usuario,
            data=request.data,
            partial=False
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            usuario = modificar_usuario(
                usuario,
                serializer.validated_data,
                request.user
            )

        except IntegrityError:
            raise BusinessException(
                "El usuario o correo ya existe."
            )

        return Response(
            {
                "success": True,
                "message": "Usuario actualizado correctamente.",
                "data": UsuarioReadSerializer(
                    usuario
                ).data
            },
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=["post"]
    )
    def activar(
        self,
        request,
        pk=None
    ):

        usuario = self.get_object()

        validar_no_automodificacion(
            request.user,
            usuario
        )

        validar_jerarquia(
            request.user,
            usuario
        )

        usuario = activar_usuario(
            usuario,
            request.user
        )

        return Response(
            {
                "success": True,
                "message": "Usuario activado correctamente.",
                "data": UsuarioReadSerializer(
                    usuario
                ).data
            },
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=["post"]
    )
    def desactivar(
        self,
        request,
        pk=None
    ):

        usuario = self.get_object()

        validar_no_automodificacion(
            request.user,
            usuario
        )

        validar_jerarquia(
            request.user,
            usuario
        )

        usuario = desactivar_usuario(
            usuario,
            request.user
        )

        return Response(
            {
                "success": True,
                "message": "Usuario desactivado correctamente.",
                "data": UsuarioReadSerializer(
                    usuario
                ).data
            },
            status=status.HTTP_200_OK
        )


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    throttle_classes = [LoginRateThrottle]


class LogoutView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request
    ):

        refresh_token = request.data.get(
            "refresh"
        )

        if not refresh_token:

            return Response(
                {
                    "success": False,
                    "message": "El refresh token es requerido.",
                    "data": None
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            token = RefreshToken(
                refresh_token
            )

            if str(token.get("user_id")) != str(request.user.id):
                return Response(
                    {
                        "success": False,
                        "message": "El refresh token no corresponde al usuario autenticado.",
                        "data": None
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            token.blacklist()    

        except TokenError:

            return Response(
                {
                    "success": False,
                    "message": "El refresh token no es válido.",
                    "data": None
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "success": True,
                "message": "Sesión cerrada correctamente.",
                "data": None
            },
            status=status.HTTP_200_OK
        )


class MeView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request
    ):

        u = request.user

        if not u.activo:

            return Response(
                {
                    "success": False,
                    "message": "El usuario está inactivo.",
                    "data": None
                },
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(
            {
                "success": True,
                "message": "Usuario obtenido correctamente.",
                "data": {
                    "id": str(u.id),
                    "nombre": u.nombre,
                    "apellido": u.apellido,
                    "usuario": u.usuario,
                    "email": u.email,
                    "rol": u.rol,
                    "activo": u.activo
                }
            },
            status=status.HTTP_200_OK
        )


class RefreshView(
    TokenRefreshView
):

    serializer_class = RefreshSerializer