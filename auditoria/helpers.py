import re

import requests


class ClienteAuditoria:
    
    

    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None

    def request(self, method, endpoint, **kwargs):
        url = f"{self.base_url}{endpoint}"

        headers = kwargs.pop("headers", {}).copy()

        if self.access_token:
            headers.setdefault(
                "Authorization",
                f"Bearer {self.access_token}"
            )

        headers.setdefault(
            "Accept",
            "application/json"
        )

        return self.session.request(
            method=method,
            url=url,
            headers=headers,
            timeout=15,
            **kwargs
        )

    def login(self, usuario, password):
        response = self.request(
            "POST",
            "/api/auth/login/",
            json={
                "usuario": usuario,
                "password": password,
            },
        )

        if response.status_code != 200:
            return response

        try:
            data = response.json()["data"]

            self.access_token = data["access"]
            self.refresh_token = data["refresh"]

        except (KeyError, TypeError, ValueError):
            pass

        return response


def parece_mensaje_en_ingles(texto):
    if not isinstance(texto, str):
        return False

    patrones = [
        r"\bthis field is required\b",
        r"\binvalid page\b",
        r"\btoken is blacklisted\b",
        r"\bgiven token not valid\b",
        r"\bnot found\b",
        r"\bnot authenticated\b",
        r"\bpermission denied\b",
        r"\bthis field may not be blank\b",
        r"\bdoes not exist\b",
    ]

    texto_normalizado = texto.lower()

    return any(
        re.search(
            patron,
            texto_normalizado
        )
        for patron in patrones
    )


def respuesta_json(response):
    try:
        return response.json()
    except ValueError:
        return None


def tiene_contrato_base(data, requiere_message=False):
    if not isinstance(data, dict):
        return False

    if "success" not in data:
        return False

    if requiere_message and "message" not in data:
        return False

    return True


def analizar_respuesta(response):
    hallazgos = []

    # ---------------------------------------------------------
    # ERRORES 5XX
    # ---------------------------------------------------------

    if response.status_code >= 500:
        hallazgos.append(
            f"Error interno del servidor: HTTP {response.status_code}"
        )

    # ---------------------------------------------------------
    # JSON
    # ---------------------------------------------------------

    data = respuesta_json(response)

    if data is None:
        hallazgos.append(
            "La respuesta no contiene JSON válido."
        )
        return hallazgos

    # ---------------------------------------------------------
    # RESPUESTA PAGINADA
    # ---------------------------------------------------------

    es_paginada = (
        isinstance(data, dict)
        and "count" in data
        and "results" in data
        and "next" in data
        and "previous" in data
    )

    if es_paginada:

        if not isinstance(data["count"], int):
            hallazgos.append(
                "El campo 'count' de la respuesta paginada "
                "no es entero."
            )

        if not isinstance(data["results"], list):
            hallazgos.append(
                "El campo 'results' de la respuesta paginada "
                "no es una lista."
            )

        if data["count"] < 0:
            hallazgos.append(
                "El campo 'count' de la respuesta paginada "
                "es negativo."
            )

        return hallazgos

    # ---------------------------------------------------------
    # CONTRATO BASE
    # ---------------------------------------------------------

    es_error_http = response.status_code >= 400

    if not tiene_contrato_base(
        data,
        requiere_message=es_error_http
    ):
        hallazgos.append(
            "La respuesta no contiene el contrato esperado."
        )
        return hallazgos

    # ---------------------------------------------------------
    # MENSAJES
    # ---------------------------------------------------------

    message = data.get("message")

    if message and parece_mensaje_en_ingles(message):
        hallazgos.append(
            f"Posible mensaje en inglés: {message!r}"
        )

    # ---------------------------------------------------------
    # CONSISTENCIA HTTP / SUCCESS
    # ---------------------------------------------------------

    success = data.get("success")

    if es_error_http and success is True:
        hallazgos.append(
            "La respuesta tiene HTTP de error "
            "pero success=true."
        )

    if not es_error_http and success is False:
        hallazgos.append(
            "La respuesta tiene HTTP exitoso "
            "pero success=false."
        )

    return hallazgos


def crear_cliente_autenticado(base_url, usuario, password):
        cliente = ClienteAuditoria(base_url)

        response = cliente.login(
            usuario,
            password,
        )

        return cliente, response