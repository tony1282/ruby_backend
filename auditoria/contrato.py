class Expectativa:

    def __init__(
        self,
        status=None,
        success=None,
        message=None,
        message_contains=None,
    ):
        self.status = status
        self.success = success
        self.message = message
        self.message_contains = message_contains


def validar_expectativa(response, expectativa):
    hallazgos = []

    # ---------------------------------------------------------
    # HTTP STATUS
    # ---------------------------------------------------------

    if (
        expectativa.status is not None
        and response.status_code != expectativa.status
    ):
        hallazgos.append(
            f"HTTP esperado {expectativa.status}, "
            f"obtenido {response.status_code}."
        )

    # ---------------------------------------------------------
    # JSON
    # ---------------------------------------------------------

    try:
        data = response.json()

    except ValueError:
        hallazgos.append(
            "La respuesta no contiene JSON válido."
        )
        return hallazgos

    # ---------------------------------------------------------
    # SUCCESS
    # ---------------------------------------------------------

    if (
        expectativa.success is not None
        and data.get("success") != expectativa.success
    ):
        hallazgos.append(
            f"success esperado {expectativa.success}, "
            f"obtenido {data.get('success')!r}."
        )

    # ---------------------------------------------------------
    # MESSAGE EXACTO
    # ---------------------------------------------------------

    if (
        expectativa.message is not None
        and data.get("message") != expectativa.message
    ):
        hallazgos.append(
            "El mensaje no coincide con el esperado. "
            f"Esperado: {expectativa.message!r}. "
            f"Obtenido: {data.get('message')!r}."
        )

    # ---------------------------------------------------------
    # MESSAGE CONTIENE
    # ---------------------------------------------------------

    if (
        expectativa.message_contains is not None
        and expectativa.message_contains
        not in str(data.get("message", ""))
    ):
        hallazgos.append(
            "El mensaje no contiene el texto esperado. "
            f"Esperado: {expectativa.message_contains!r}. "
            f"Obtenido: {data.get('message')!r}."
        )

    return hallazgos