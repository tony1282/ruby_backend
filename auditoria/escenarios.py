from auditoria.helpers import (
    ClienteAuditoria,
    analizar_respuesta,
    crear_cliente_autenticado,
)

from auditoria.contrato import (
    Expectativa,
    validar_expectativa,
)


def ejecutar_prueba(
    resultados,
    cliente,
    metodo,
    endpoint,
    nombre,
):
    try:
        response = cliente.request(
            metodo,
            endpoint,
        )

        hallazgos = analizar_respuesta(response)

        if hallazgos:
            resultados.fail_test(
                nombre,
                " | ".join(hallazgos),
            )

            return response

        resultados.pass_test(
            nombre,
            f"HTTP {response.status_code}",
        )

        return response

    except Exception as exc:
        resultados.error_test(
            nombre,
            f"{type(exc).__name__}: {exc}",
        )

        return None


def ejecutar_prueba_contrato(
    resultados,
    cliente,
    metodo,
    endpoint,
    nombre,
    expectativa,
):
    try:
        response = cliente.request(
            metodo,
            endpoint,
        )

        hallazgos = validar_expectativa(
            response,
            expectativa,
        )

        if hallazgos:
            resultados.fail_test(
                nombre,
                " | ".join(hallazgos),
            )
        else:
            resultados.pass_test(
                nombre,
                f"HTTP {response.status_code}",
            )

        return response

    except Exception as exc:
        resultados.error_test(
            nombre,
            f"{type(exc).__name__}: {exc}",
        )

        return None


# ==============================================================
# ENDPOINTS DE SOLO LECTURA
# ==============================================================

def auditar_lecturas(resultados, cliente):
    pruebas = [
        (
            "GET",
            "/api/empresa",
            "GET Empresa",
        ),
        (
            "GET",
            "/api/metodos-pago/",
            "GET Métodos de pago",
        ),
        (
            "GET",
            "/api/metodos-pago/activos/",
            "GET Métodos de pago activos",
        ),
        (
            "GET",
            "/api/bitacora/",
            "GET Bitácora",
        ),
        (
            "GET",
            "/api/reportes/resumen-dia/",
            "GET Reporte resumen día",
        ),
        (
            "GET",
            "/api/reportes/ventas/",
            "GET Reporte ventas",
        ),
        (
            "GET",
            "/api/reportes/productos/",
            "GET Reporte productos",
        ),
        (
            "GET",
            "/api/reportes/inventario/",
            "GET Reporte inventario",
        ),
        (
            "GET",
            "/api/reportes/stock-bajo/",
            "GET Reporte stock bajo",
        ),
        (
            "GET",
            "/api/reportes/cortes/",
            "GET Reporte cortes",
        ),
        (
            "GET",
            "/api/reportes/devoluciones/",
            "GET Reporte devoluciones",
        ),
        (
            "GET",
            "/api/reportes/garantias/",
            "GET Reporte garantías",
        ),
        (
            "GET",
            "/api/reportes/movimientos/",
            "GET Reporte movimientos",
        ),
    ]

    for metodo, endpoint, nombre in pruebas:
        ejecutar_prueba(
            resultados,
            cliente,
            metodo,
            endpoint,
            nombre,
        )


# ==============================================================
# PAGINACIÓN
# ==============================================================

def auditar_paginacion(resultados, cliente):
    pruebas = [
        (
            "GET",
            "/api/bitacora/?page=0",
            "Bitácora — page=0",
        ),
        (
            "GET",
            "/api/bitacora/?page=-1",
            "Bitácora — page=-1",
        ),
        (
            "GET",
            "/api/bitacora/?page=999999",
            "Bitácora — página inexistente",
        ),
        (
            "GET",
            "/api/bitacora/?page=abc",
            "Bitácora — page inválido",
        ),
        (
            "GET",
            "/api/bitacora/?page_size=1",
            "Bitácora — page_size=1",
        ),
        (
            "GET",
            "/api/bitacora/?page_size=50",
            "Bitácora — page_size=50",
        ),
        (
            "GET",
            "/api/bitacora/?page_size=200",
            "Bitácora — page_size=200",
        ),
        (
            "GET",
            "/api/bitacora/?page_size=201",
            "Bitácora — page_size=201",
        ),
        (
            "GET",
            "/api/reportes/ventas/?page=0",
            "Reporte ventas — page=0",
        ),
        (
            "GET",
            "/api/reportes/ventas/?page=999999",
            "Reporte ventas — página inexistente",
        ),
        (
            "GET",
            "/api/reportes/ventas/?page=abc",
            "Reporte ventas — page inválido",
        ),
        (
            "GET",
            "/api/reportes/ventas/?page_size=1",
            "Reporte ventas — page_size=1",
        ),
        (
            "GET",
            "/api/reportes/ventas/?page_size=200",
            "Reporte ventas — page_size=200",
        ),
        (
            "GET",
            "/api/reportes/ventas/?page_size=201",
            "Reporte ventas — page_size=201",
        ),
    ]

    for metodo, endpoint, nombre in pruebas:
        ejecutar_prueba(
            resultados,
            cliente,
            metodo,
            endpoint,
            nombre,
        )


# ==============================================================
# FILTROS DE BITÁCORA
# ==============================================================

def auditar_filtros_bitacora(
    resultados,
    cliente,
    usuario_id_auditor=None,
    usuario_login_auditor=None,
    usuario_nombre_auditor=None,
):
    try:
        response = cliente.request(
            "GET",
            "/api/bitacora/?page_size=50",
        )

        if response.status_code != 200:
            resultados.error_test(
                "Bitácora — preparación de filtros",
                "No fue posible obtener registros base. "
                f"HTTP {response.status_code}",
            )

            return

        data = response.json()
        registros = data.get("results", [])

        if not isinstance(registros, list) or not registros:
            resultados.error_test(
                "Bitácora — preparación de filtros",
                "No existen registros suficientes para probar "
                "semánticamente los filtros.",
            )

            return

    except Exception as exc:
        resultados.error_test(
            "Bitácora — preparación de filtros",
            f"{type(exc).__name__}: {exc}",
        )

        return

    modulo_real = None
    accion_real = None

    for registro in registros:
        if modulo_real is None:
            valor = registro.get("modulo")

            if isinstance(valor, str) and valor.strip():
                modulo_real = valor

        if accion_real is None:
            valor = registro.get("accion")

            if isinstance(valor, str) and valor.strip():
                accion_real = valor

    # ==========================================================
    # VALIDACIONES DE PARÁMETROS
    # ==========================================================

    ejecutar_prueba(
        resultados,
        cliente,
        "GET",
        "/api/bitacora/?usuario=abc",
        "Bitácora — usuario inválido",
    )

    ejecutar_prueba(
        resultados,
        cliente,
        "GET",
        "/api/bitacora/?usuario=123",
        "Bitácora — usuario numérico inválido",
    )

    ejecutar_prueba(
        resultados,
        cliente,
        "GET",
        "/api/bitacora/"
        "?usuario=00000000-0000-0000-0000-000000000000",
        "Bitácora — usuario UUID inexistente",
    )

    ejecutar_prueba(
        resultados,
        cliente,
        "GET",
        "/api/bitacora/?fecha_desde=2026-99-99",
        "Bitácora — fecha_desde inválida",
    )

    ejecutar_prueba(
        resultados,
        cliente,
        "GET",
        "/api/bitacora/?fecha_desde=abc",
        "Bitácora — fecha_desde texto inválido",
    )

    ejecutar_prueba(
        resultados,
        cliente,
        "GET",
        "/api/bitacora/?fecha_hasta=2026-99-99",
        "Bitácora — fecha_hasta inválida",
    )

    ejecutar_prueba(
        resultados,
        cliente,
        "GET",
        "/api/bitacora/?fecha_hasta=abc",
        "Bitácora — fecha_hasta texto inválido",
    )

    ejecutar_prueba(
        resultados,
        cliente,
        "GET",
        "/api/bitacora/"
        "?fecha_desde=2026-12-31"
        "&fecha_hasta=2026-01-01",
        "Bitácora — rango de fechas invertido",
    )

    # ==========================================================
    # FILTRO SEMÁNTICO — MÓDULO
    # ==========================================================

    if modulo_real is None:
        resultados.error_test(
            "Bitácora — filtro semántico módulo",
            "No se encontró un módulo real en los registros.",
        )

    else:
        try:
            response = cliente.request(
                "GET",
                f"/api/bitacora/?modulo={modulo_real}",
            )

            data = response.json()

            if response.status_code != 200:
                resultados.fail_test(
                    "Bitácora — filtro semántico módulo",
                    f"HTTP {response.status_code}",
                )

            else:
                resultados_filtrados = data.get("results", [])

                incorrectos = [
                    registro
                    for registro in resultados_filtrados
                    if registro.get("modulo") != modulo_real
                ]

                if incorrectos:
                    resultados.fail_test(
                        "Bitácora — filtro semántico módulo",
                        "El filtro devolvió "
                        f"{len(incorrectos)} registros "
                        "que no pertenecen al módulo "
                        f"{modulo_real!r}.",
                    )

                else:
                    resultados.pass_test(
                        "Bitácora — filtro semántico módulo",
                        "Todos los registros cumplen "
                        f"modulo={modulo_real!r}.",
                    )

        except Exception as exc:
            resultados.error_test(
                "Bitácora — filtro semántico módulo",
                f"{type(exc).__name__}: {exc}",
            )

    # ==========================================================
    # FILTRO SEMÁNTICO — ACCIÓN
    # ==========================================================

    if accion_real is None:
        resultados.error_test(
            "Bitácora — filtro semántico acción",
            "No se encontró una acción real en los registros.",
        )

    else:
        try:
            response = cliente.request(
                "GET",
                f"/api/bitacora/?accion={accion_real}",
            )

            data = response.json()

            if response.status_code != 200:
                resultados.fail_test(
                    "Bitácora — filtro semántico acción",
                    f"HTTP {response.status_code}",
                )

            else:
                resultados_filtrados = data.get("results", [])

                incorrectos = [
                    registro
                    for registro in resultados_filtrados
                    if registro.get("accion") != accion_real
                ]

                if incorrectos:
                    resultados.fail_test(
                        "Bitácora — filtro semántico acción",
                        "El filtro devolvió "
                        f"{len(incorrectos)} registros "
                        "con una acción diferente a "
                        f"{accion_real!r}.",
                    )

                else:
                    resultados.pass_test(
                        "Bitácora — filtro semántico acción",
                        "Todos los registros cumplen "
                        f"accion={accion_real!r}.",
                    )

        except Exception as exc:
            resultados.error_test(
                "Bitácora — filtro semántico acción",
                f"{type(exc).__name__}: {exc}",
            )

    # ==========================================================
    # FILTRO SEMÁNTICO — USUARIO
    # ==========================================================

    if not usuario_id_auditor:
        resultados.error_test(
            "Bitácora — filtro semántico usuario",
            "No fue posible obtener el ID del usuario autenticado.",
        )

    elif not usuario_nombre_auditor:
        resultados.error_test(
            "Bitácora — filtro semántico usuario",
            "No fue posible obtener el nombre completo "
            "del usuario autenticado.",
        )

    else:
        try:
            response = cliente.request(
                "GET",
                "/api/bitacora/"
                f"?usuario={usuario_id_auditor}",
            )

            data = response.json()

            if response.status_code != 200:
                resultados.fail_test(
                    "Bitácora — filtro semántico usuario",
                    f"HTTP {response.status_code}",
                )

            else:
                resultados_filtrados = data.get("results", [])

                if not isinstance(resultados_filtrados, list):
                    resultados.fail_test(
                        "Bitácora — filtro semántico usuario",
                        "La respuesta no contiene una lista "
                        "en 'results'.",
                    )

                elif not resultados_filtrados:
                    resultados.fail_test(
                        "Bitácora — filtro semántico usuario",
                        "El filtro por el usuario autenticado "
                        "no devolvió registros.",
                    )

                else:
                    incorrectos = [
                        registro
                        for registro in resultados_filtrados
                        if registro.get("usuario")
                        != usuario_nombre_auditor
                    ]

                    if incorrectos:
                        resultados.fail_test(
                            "Bitácora — filtro semántico usuario",
                            "El filtro devolvió "
                            f"{len(incorrectos)} registros "
                            "que no corresponden al usuario "
                            f"{usuario_nombre_auditor!r}.",
                        )

                    else:
                        resultados.pass_test(
                            "Bitácora — filtro semántico usuario",
                            "Todos los registros devueltos "
                            "corresponden al usuario autenticado "
                            f"{usuario_nombre_auditor!r}.",
                        )

        except Exception as exc:
            resultados.error_test(
                "Bitácora — filtro semántico usuario",
                f"{type(exc).__name__}: {exc}",
            )

    # ==========================================================
    # FILTROS COMBINADOS
    # ==========================================================

    if modulo_real is not None and accion_real is not None:
        try:
            response = cliente.request(
                "GET",
                "/api/bitacora/"
                f"?modulo={modulo_real}"
                f"&accion={accion_real}",
            )

            data = response.json()

            if response.status_code != 200:
                resultados.fail_test(
                    "Bitácora — filtros combinados",
                    f"HTTP {response.status_code}",
                )

            else:
                resultados_filtrados = data.get("results", [])

                incorrectos = [
                    registro
                    for registro in resultados_filtrados
                    if (
                        registro.get("modulo") != modulo_real
                        or registro.get("accion") != accion_real
                    )
                ]

                if incorrectos:
                    resultados.fail_test(
                        "Bitácora — filtros combinados",
                        f"{len(incorrectos)} registros "
                        "no cumplen todos los filtros.",
                    )

                else:
                    resultados.pass_test(
                        "Bitácora — filtros combinados",
                        "Todos los registros cumplen "
                        "módulo y acción.",
                    )

        except Exception as exc:
            resultados.error_test(
                "Bitácora — filtros combinados",
                f"{type(exc).__name__}: {exc}",
            )


# ==============================================================
# AUTENTICACIÓN
# ==============================================================

def auditar_autenticacion(resultados, cliente):
    endpoints = [
        ("/api/auth/me/", "Auth me"),
        ("/api/empresa", "Empresa"),
        ("/api/metodos-pago/", "Métodos de pago"),
        ("/api/bitacora/", "Bitácora"),
        ("/api/reportes/resumen-dia/", "Reporte resumen día"),
        ("/api/reportes/ventas/", "Reporte ventas"),
        ("/api/reportes/productos/", "Reporte productos"),
        ("/api/reportes/inventario/", "Reporte inventario"),
        ("/api/reportes/stock-bajo/", "Reporte stock bajo"),
        ("/api/reportes/cortes/", "Reporte cortes"),
        ("/api/reportes/devoluciones/", "Reporte devoluciones"),
        ("/api/reportes/garantias/", "Reporte garantías"),
        ("/api/reportes/movimientos/", "Reporte movimientos"),
    ]

    token_original = cliente.access_token
    refresh_original = cliente.refresh_token

    try:
        cliente.access_token = None

        for endpoint, nombre in endpoints:
            try:
                response = cliente.request(
                    "GET",
                    endpoint,
                )

                if response.status_code != 401:
                    resultados.fail_test(
                        f"Sin autenticación — {nombre}",
                        f"Se esperaba HTTP 401, "
                        f"se obtuvo HTTP {response.status_code}.",
                    )
                    continue

                hallazgos = analizar_respuesta(response)

                if hallazgos:
                    resultados.fail_test(
                        f"Sin autenticación — {nombre}",
                        " | ".join(hallazgos),
                    )
                    continue

                resultados.pass_test(
                    f"Sin autenticación — {nombre}",
                    "HTTP 401 correctamente.",
                )

            except Exception as exc:
                resultados.error_test(
                    f"Sin autenticación — {nombre}",
                    f"{type(exc).__name__}: {exc}",
                )

        cliente.access_token = "token_completamente_invalido"

        for endpoint, nombre in endpoints:
            try:
                response = cliente.request(
                    "GET",
                    endpoint,
                )

                if response.status_code != 401:
                    resultados.fail_test(
                        f"Token inválido — {nombre}",
                        f"Se esperaba HTTP 401, "
                        f"se obtuvo HTTP {response.status_code}.",
                    )
                    continue

                hallazgos = analizar_respuesta(response)

                if hallazgos:
                    resultados.fail_test(
                        f"Token inválido — {nombre}",
                        " | ".join(hallazgos),
                    )
                    continue

                resultados.pass_test(
                    f"Token inválido — {nombre}",
                    "HTTP 401 correctamente.",
                )

            except Exception as exc:
                resultados.error_test(
                    f"Token inválido — {nombre}",
                    f"{type(exc).__name__}: {exc}",
                )

    finally:
        cliente.access_token = token_original
        cliente.refresh_token = refresh_original


# ==============================================================
# ROLES
# ==============================================================

def auditar_roles(
    resultados,
    base_url,
    credenciales,
):
    clientes = {}

    for rol, datos in credenciales.items():
        usuario = datos.get("usuario")
        password = datos.get("password")

        if not usuario or not password:
            resultados.error_test(
                f"Autenticación — {rol}",
                "Faltan credenciales de auditoría.",
            )
            continue

        cliente, response = crear_cliente_autenticado(
            base_url,
            usuario,
            password,
        )

        if response.status_code != 200 or not cliente.access_token:
            resultados.fail_test(
                f"Autenticación — {rol}",
                f"HTTP {response.status_code}: "
                f"{response.text[:300]}",
            )
            continue

        clientes[rol] = cliente

        resultados.pass_test(
            f"Autenticación — {rol}",
            "Login correcto.",
        )

    endpoints_lectura = [
        ("/api/auth/me/", "Auth me"),
        ("/api/empresa", "Empresa"),
        ("/api/metodos-pago/", "Métodos de pago"),
        ("/api/metodos-pago/activos/", "Métodos de pago activos"),
        ("/api/bitacora/", "Bitácora"),
        ("/api/reportes/resumen-dia/", "Reporte resumen día"),
        ("/api/reportes/ventas/", "Reporte ventas"),
        ("/api/reportes/productos/", "Reporte productos"),
        ("/api/reportes/inventario/", "Reporte inventario"),
        ("/api/reportes/stock-bajo/", "Reporte stock bajo"),
        ("/api/reportes/cortes/", "Reporte cortes"),
        ("/api/reportes/devoluciones/", "Reporte devoluciones"),
        ("/api/reportes/garantias/", "Reporte garantías"),
        ("/api/reportes/movimientos/", "Reporte movimientos"),
    ]

    for rol, cliente in clientes.items():
        for endpoint, nombre in endpoints_lectura:
            try:
                response = cliente.request(
                    "GET",
                    endpoint,
                )

                if response.status_code not in (200, 403):
                    resultados.fail_test(
                        f"Rol {rol} — GET {nombre}",
                        f"HTTP inesperado: "
                        f"{response.status_code}",
                    )
                    continue

                resultados.pass_test(
                    f"Rol {rol} — GET {nombre}",
                    f"HTTP {response.status_code}",
                )

            except Exception as exc:
                resultados.error_test(
                    f"Rol {rol} — GET {nombre}",
                    f"{type(exc).__name__}: {exc}",
                )


# ==============================================================
# PILOTO DE CONTRATOS
# ==============================================================

def auditar_piloto_contrato(
    resultados,
    base_url,
    credenciales,
):
    # ==========================================================
    # AUTH-001 — SIN AUTENTICACIÓN
    # ==========================================================

    cliente = ClienteAuditoria(base_url)

    cliente.access_token = None

    ejecutar_prueba_contrato(
        resultados,
        cliente,
        "GET",
        "/api/auth/me/",
        "AUTH-001 — Sin autenticación",
        Expectativa(
            status=401,
            success=False,
        ),
    )

    # ==========================================================
    # AUTH-002 — TOKEN INVÁLIDO
    # ==========================================================

    cliente.access_token = "token_completamente_invalido"

    ejecutar_prueba_contrato(
        resultados,
        cliente,
        "GET",
        "/api/auth/me/",
        "AUTH-002 — Token inválido",
        Expectativa(
            status=401,
            success=False,
        ),
    )

    # ==========================================================
    # AUTH-003 — LOGIN EMPLEADO
    # ==========================================================

    datos = credenciales.get("empleado", {})

    usuario = datos.get("usuario")
    password = datos.get("password")

    if not usuario or not password:
        resultados.sin_regla(
            "AUTH-003 — Login empleado",
            "No existen credenciales configuradas.",
        )
        return

    cliente_empleado, response = crear_cliente_autenticado(
        base_url,
        usuario,
        password,
    )

    if response.status_code != 200 or not cliente_empleado.access_token:
        resultados.fail_test(
            "AUTH-003 — Login empleado",
            f"HTTP {response.status_code}.",
        )
        return

    resultados.pass_test(
        "AUTH-003 — Login empleado",
        "Login correcto.",
    )

    # ==========================================================
    # AUTH-004 — EMPLEADO NO PUEDE REPORTE DE VENTAS
    # ==========================================================

    ejecutar_prueba_contrato(
        resultados,
        cliente_empleado,
        "GET",
        "/api/reportes/ventas/",
        "AUTH-004 — Empleado — Reporte ventas",
        Expectativa(
            status=403,
            success=False,
        ),
    )

    # ==========================================================
    # AUTH-005 — EMPLEADO PUEDE REPORTE DE INVENTARIO
    # ==========================================================

    ejecutar_prueba_contrato(
        resultados,
        cliente_empleado,
        "GET",
        "/api/reportes/inventario/",
        "AUTH-005 — Empleado — Reporte inventario",
        Expectativa(
            status=200,
        ),
    )
    
# ==============================================================
# IDOR / AUTORIZACIÓN HORIZONTAL
# ==============================================================

def auditar_idor(
    resultados,
    base_url,
    credenciales,
    recursos,
):
    """
    Pruebas de acceso horizontal entre usuarios.

    La función NO crea ni modifica datos.
    Utiliza únicamente recursos preparados por la auditoría.

    Estructura esperada de 'recursos':

    {
        "venta_empleado_b": "<uuid>",
        "corte_empleado_b": "<uuid>",
        "devolucion_empleado_b": "<uuid>",
        "garantia_empleado_b": "<uuid>",
        "ticket_venta_empleado_b": "<uuid>",
        "detalle_venta_empleado_b": "<uuid>",
    }
    """

    datos_a = credenciales.get("empleado_a", {})
    datos_b = credenciales.get("empleado_b", {})

    usuario_a = datos_a.get("usuario")
    password_a = datos_a.get("password")

    usuario_b = datos_b.get("usuario")
    password_b = datos_b.get("password")

    if not usuario_a or not password_a:
        resultados.sin_regla(
            "IDOR-001 — Empleado A",
            "No existen credenciales configuradas.",
        )
        return

    if not usuario_b or not password_b:
        resultados.sin_regla(
            "IDOR-002 — Empleado B",
            "No existen credenciales configuradas.",
        )
        return

    # ==========================================================
    # LOGIN EMPLEADO A
    # ==========================================================

    cliente_a, response_a = crear_cliente_autenticado(
        base_url,
        usuario_a,
        password_a,
    )

    if response_a.status_code != 200 or not cliente_a.access_token:
        resultados.error_test(
            "IDOR-001 — Login Empleado A",
            f"HTTP {response_a.status_code}.",
        )
        return

    resultados.pass_test(
        "IDOR-001 — Login Empleado A",
        "Login correcto.",
    )

    # ==========================================================
    # LOGIN EMPLEADO B
    # ==========================================================

    cliente_b, response_b = crear_cliente_autenticado(
        base_url,
        usuario_b,
        password_b,
    )

    if response_b.status_code != 200 or not cliente_b.access_token:
        resultados.error_test(
            "IDOR-002 — Login Empleado B",
            f"HTTP {response_b.status_code}.",
        )
        return

    resultados.pass_test(
        "IDOR-002 — Login Empleado B",
        "Login correcto.",
    )

    # ==========================================================
    # RECURSOS DEL EMPLEADO B
    # ==========================================================

    pruebas = [
        (
            "GET",
            "venta_empleado_b",
            "/api/ventas/{id}/",
            "IDOR-003 — Empleado A → Venta de B",
        ),
        (
            "GET",
            "corte_empleado_b",
            "/api/corte-caja/{id}/",
            "IDOR-004 — Empleado A → Corte de B",
        ),
        (
            "GET",
            "devolucion_empleado_b",
            "/api/devoluciones/{id}/",
            "IDOR-005 — Empleado A → Devolución de B",
        ),
        (
            "GET",
            "garantia_empleado_b",
            "/api/garantias/{id}/",
            "IDOR-006 — Empleado A → Garantía de B",
        ),
        (
            "GET",
            "ticket_venta_empleado_b",
            "/api/tickets/{id}/",
            "IDOR-007 — Empleado A → Ticket de B",
        ),
        (
            "GET",
            "detalle_venta_empleado_b",
            "/api/detalle-venta/{id}/",
            "IDOR-008 — Empleado A → DetalleVenta de B",
        ),
    ]

    for metodo, recurso, endpoint, nombre in pruebas:
        recurso_id = recursos.get(recurso)

        if not recurso_id:
            resultados.sin_regla(
                nombre,
                f"No existe recurso preparado: {recurso}.",
            )
            continue

        endpoint_final = endpoint.format(
            id=recurso_id,
        )

        response = ejecutar_prueba_contrato(
            resultados,
            cliente_a,
            metodo,
            endpoint_final,
            nombre,
            Expectativa(
                status=403,
                success=False,
            ),
        )