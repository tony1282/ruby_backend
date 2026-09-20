from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound


class BusinessException(Exception):
    """
    Excepción para errores de negocio esperados.

    Debe lanzarse cuando una operación no puede completarse
    por una regla de negocio (estado inválido, stock insuficiente,
    plazo vencido, etc.).
    """

    def __init__(self, message, data=None):

        super().__init__(message)

        self.data = data


def custom_exception_handler(exc, context):
    """
    Manejador global de excepciones de Django REST Framework.

    Estandariza las respuestas automáticas del POS:

    {
        "success": False,
        "message": "...",
        "data": ...
    }
    """

    # ----------------------------------------------------------
    # EXCEPCIONES DE NEGOCIO
    # ----------------------------------------------------------

    if isinstance(exc, BusinessException):

        return Response(
            {
                "success": False,
                "message": str(exc),
                "data": exc.data
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # ----------------------------------------------------------
    # EXCEPCIONES DRF
    # ----------------------------------------------------------

    response = exception_handler(
        exc,
        context
    )

    # Si DRF no sabe manejar la excepción,
    # dejamos que continúe su comportamiento normal.
    if response is None:
        return response

    # ----------------------------------------------------------
    # RECURSO NO ENCONTRADO
    # ----------------------------------------------------------
    
    if response.status_code == status.HTTP_404_NOT_FOUND:

        response.data = {
            "success": False,
            "message": "El recurso solicitado no existe.",
            "data": None,
        }

        return response

    # ----------------------------------------------------------
    # OBTENER MENSAJE
    # ----------------------------------------------------------

    if isinstance(response.data, dict):

        message = response.data.get("detail")

        if message is None:

            # Errores de validación de DRF
            message = "La solicitud no es válida."

            data = response.data

        else:

            data = None

    else:

        message = str(response.data)

        data = None

    # ----------------------------------------------------------
    # RESPUESTA ESTÁNDAR DEL POS
    # ----------------------------------------------------------

    response.data = {
        "success": False,
        "message": str(message),
        "data": data,
    }

    return response