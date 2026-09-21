import os
from dotenv import load_dotenv

load_dotenv()
from auditoria.helpers import (
    ClienteAuditoria,
    analizar_respuesta,
)
from auditoria.resultados import ResultadosAuditoria
from auditoria.escenarios import (
    auditar_lecturas,
    auditar_paginacion,
    auditar_filtros_bitacora,
    auditar_autenticacion,
    auditar_roles,
    auditar_piloto_contrato,
)


BASE_URL = os.getenv(
    "AUDITORIA_BASE_URL",
    "http://127.0.0.1:8000"
)


credenciales_roles = {
    "superadmin": {
        "usuario": os.getenv(
            "AUDITORIA_SUPERADMIN_USUARIO"
        ),
        "password": os.getenv(
            "AUDITORIA_SUPERADMIN_PASSWORD"
        ),
    },
    "admin": {
        "usuario": os.getenv(
            "AUDITORIA_ADMIN_USUARIO"
        ),
        "password": os.getenv(
            "AUDITORIA_ADMIN_PASSWORD"
        ),
    },
    "empleado": {
        "usuario": os.getenv(
            "AUDITORIA_EMPLEADO_USUARIO"
        ),
        "password": os.getenv(
            "AUDITORIA_EMPLEADO_PASSWORD"
        ),
    },
    "empleado_a": {
        "usuario": os.getenv(
            "AUDITORIA_EMPLEADO_A_USUARIO"
        ),
        "password": os.getenv(
            "AUDITORIA_EMPLEADO_A_PASSWORD"
        ),
    },
    "empleado_b": {
        "usuario": os.getenv(
            "AUDITORIA_EMPLEADO_B_USUARIO"
        ),
        "password": os.getenv(
            "AUDITORIA_EMPLEADO_B_PASSWORD"
        ),
    },
}


AUDITORIA_USUARIO = os.getenv(
    "AUDITORIA_USUARIO"
)

AUDITORIA_PASSWORD = os.getenv(
    "AUDITORIA_PASSWORD"
)


def registrar_analisis(
    resultados,
    nombre,
    response
):
    hallazgos = analizar_respuesta(
        response
    )

    if hallazgos:
        resultados.fail_test(
            nombre,
            " | ".join(hallazgos)
        )
        return False

    resultados.pass_test(
        nombre,
        f"HTTP {response.status_code}"
    )

    return True


def main():
    resultados = ResultadosAuditoria()
    cliente = ClienteAuditoria(
        BASE_URL
    )

    print("=" * 60)
    print("RUBY — MEGA AUDITORÍA")
    print("=" * 60)
    print(
        f"Backend: {BASE_URL}"
    )

    # ==========================================================
    # CONFIGURACIÓN
    # ==========================================================

    if (
        not AUDITORIA_USUARIO
        or not AUDITORIA_PASSWORD
    ):
        resultados.error_test(
            "Configuración de credenciales",
            "Faltan AUDITORIA_USUARIO o AUDITORIA_PASSWORD."
        )

        resultados.imprimir_resumen()
        return

    # ==========================================================
    # AUTENTICACIÓN DEL AUDITOR
    # ==========================================================

    try:
        response = cliente.login(
            AUDITORIA_USUARIO,
            AUDITORIA_PASSWORD,
        )

        if (
            response.status_code == 200
            and cliente.access_token
        ):
            resultados.pass_test(
                "Autenticación del auditor",
                "Access token obtenido correctamente."
            )

        else:
            resultados.fail_test(
                "Autenticación del auditor",
                f"HTTP {response.status_code}: "
                f"{response.text[:300]}"
            )

            resultados.imprimir_resumen()
            return

    except Exception as exc:
        resultados.error_test(
            "Autenticación del auditor",
            f"{type(exc).__name__}: {exc}"
        )

        resultados.imprimir_resumen()
        return

    # ==========================================================
    # DATOS DEL USUARIO AUTENTICADO
    # ==========================================================

    usuario_id_auditor = None
    usuario_login_auditor = None
    usuario_nombre_auditor = None

    try:
        response = cliente.request(
            "GET",
            "/api/auth/me/"
        )

        registrar_analisis(
            resultados,
            "GET /api/auth/me/",
            response
        )

        data = response.json()

        if (
            isinstance(data, dict)
            and isinstance(
                data.get("data"),
                dict
            )
        ):
            usuario_data = data["data"]

            usuario_id_auditor = (
                usuario_data.get("id")
            )

            usuario_login_auditor = (
                usuario_data.get("usuario")
            )

            nombre = usuario_data.get(
                "nombre",
                ""
            )

            apellido = usuario_data.get(
                "apellido",
                ""
            )

            usuario_nombre_auditor = (
                f"{nombre} {apellido}"
            ).strip()

        if not usuario_id_auditor:
            resultados.error_test(
                "Identificación del usuario auditor",
                "GET /api/auth/me/ no devolvió "
                "el ID del usuario."
            )

        if not usuario_login_auditor:
            resultados.error_test(
                "Identificación del usuario auditor",
                "GET /api/auth/me/ no devolvió "
                "el usuario."
            )

        if not usuario_nombre_auditor:
            resultados.error_test(
                "Identificación del usuario auditor",
                "GET /api/auth/me/ no devolvió "
                "nombre y apellido del usuario."
            )

    except Exception as exc:
        resultados.error_test(
            "GET /api/auth/me/",
            f"{type(exc).__name__}: {exc}"
        )

    # ==========================================================
    # PILOTO DE CONTRATOS
    # ==========================================================

    print(
        "\n" + "-" * 60
    )

    print(
        "AUDITORÍA — PILOTO DE CONTRATOS"
    )

    print(
        "-" * 60
    )

    auditar_piloto_contrato(
        resultados,
        BASE_URL,
        credenciales_roles,
    )

    # ==========================================================
    # AUTENTICACIÓN Y TOKEN
    # ==========================================================

    print(
        "\n" + "-" * 60
    )

    print(
        "AUDITORÍA — AUTENTICACIÓN Y TOKEN"
    )

    print(
        "-" * 60
    )

    auditar_autenticacion(
        resultados,
        cliente,
    )

    # ==========================================================
    # ROLES Y AUTORIZACIÓN
    # ==========================================================

    print(
        "\n" + "-" * 60
    )

    print(
        "AUDITORÍA — ROLES Y AUTORIZACIÓN"
    )

    print(
        "-" * 60
    )

    auditar_roles(
        resultados,
        BASE_URL,
        credenciales_roles,
    )

    # ==========================================================
    # ENDPOINTS DE SOLO LECTURA
    # ==========================================================

    print(
        "\n" + "-" * 60
    )

    print(
        "AUDITORÍA — ENDPOINTS DE SOLO LECTURA"
    )

    print(
        "-" * 60
    )

    auditar_lecturas(
        resultados,
        cliente,
    )

    # ==========================================================
    # PAGINACIÓN Y PARÁMETROS EXTREMOS
    # ==========================================================

    print(
        "\n" + "-" * 60
    )

    print(
        "AUDITORÍA — PAGINACIÓN Y PARÁMETROS EXTREMOS"
    )

    print(
        "-" * 60
    )

    auditar_paginacion(
        resultados,
        cliente,
    )

    # ==========================================================
    # FILTROS DE BITÁCORA
    # ==========================================================

    print(
        "\n" + "-" * 60
    )

    print(
        "AUDITORÍA — FILTROS DE BITÁCORA"
    )

    print(
        "-" * 60
    )

    auditar_filtros_bitacora(
        resultados,
        cliente,
        usuario_id_auditor,
        usuario_login_auditor,
        usuario_nombre_auditor,
    )

    # ==========================================================
    # RESULTADO FINAL
    # ==========================================================

    resultados.imprimir_resumen()


if __name__ == "__main__":
    main()