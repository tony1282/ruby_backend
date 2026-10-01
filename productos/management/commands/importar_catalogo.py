from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from categorias.models import Categoria
from productos.models import Producto
from variantes.models import Variante


COLUMNAS_REQUERIDAS = [
    "CATEGORIA_PROVISIONAL",
    "PRODUCTO_FINAL",
    "VARIANTE_FINAL",
    "SKU_FINAL",
    "CODIGO_BARRAS_FINAL",
    "STOCK_FINAL",
    "STOCK_MINIMO_FINAL",
    "COSTO_FINAL",
    "PRECIO_MENUDEO_FINAL",
    "PRECIO_MAYOREO_FINAL",
]


def limpiar_texto(valor):
    if pd.isna(valor):
        return ""

    return str(valor).strip()


def limpiar_codigo(valor):
    """
    Limpia SKU/código de barras sin convertirlo a número.

    Importante:
    - conserva ceros a la izquierda si Excel/pandas los entrega como texto
    - convierte NaN en cadena vacía
    """

    if pd.isna(valor):
        return ""

    valor = str(valor).strip()

    # Evita valores del tipo "12345.0" cuando Excel lo interpretó
    # accidentalmente como número.
    if valor.endswith(".0"):
        parte = valor[:-2]

        if parte.isdigit():
            valor = parte

    return valor


def entero_no_negativo(valor, campo, fila_excel):
    try:
        numero = pd.to_numeric(valor, errors="raise")
    except Exception:
        raise CommandError(
            f"Fila {fila_excel}: {campo} no es numérico: {valor!r}"
        )

    if pd.isna(numero):
        numero = 0

    if numero < 0:
        raise CommandError(
            f"Fila {fila_excel}: {campo} no puede ser negativo: {numero}"
        )

    if float(numero).is_integer() is False:
        raise CommandError(
            f"Fila {fila_excel}: {campo} debe ser entero: {numero}"
        )

    return int(numero)


def decimal_no_negativo(valor, campo, fila_excel):
    if pd.isna(valor):
        return Decimal("0.00")

    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        raise CommandError(
            f"Fila {fila_excel}: {campo} no es un decimal válido: {valor!r}"
        )

    if numero < 0:
        raise CommandError(
            f"Fila {fila_excel}: {campo} no puede ser negativo: {numero}"
        )

    return numero.quantize(Decimal("0.01"))


class Command(BaseCommand):
    help = "Importa catalogo_final.xlsx al catálogo del POS"

    def add_arguments(self, parser):
        parser.add_argument(
            "archivo",
            type=str,
            help="Ruta al archivo catalogo_final.xlsx",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Valida el archivo sin insertar datos en la base de datos",
        )

    def handle(self, *args, **options):
        archivo = Path(options["archivo"])
        dry_run = options["dry_run"]

        if not archivo.exists():
            raise CommandError(
                f"No existe el archivo: {archivo}"
            )

        if archivo.suffix.lower() not in {".xlsx", ".xls"}:
            raise CommandError(
                "El archivo debe ser Excel (.xlsx o .xls)"
            )

        self.stdout.write("")
        self.stdout.write(
            self.style.NOTICE(
                f"Leyendo catálogo: {archivo}"
            )
        )

        try:
            df = pd.read_excel(
                archivo,
                dtype={
                    "SKU_FINAL": str,
                    "CODIGO_BARRAS_FINAL": str,
                },
            )
        except Exception as exc:
            raise CommandError(
                f"No se pudo leer el Excel: {exc}"
            )

        # ======================================================
        # VALIDAR COLUMNAS
        # ======================================================

        faltantes = [
            columna
            for columna in COLUMNAS_REQUERIDAS
            if columna not in df.columns
        ]

        if faltantes:
            raise CommandError(
                "Faltan columnas obligatorias:\n- "
                + "\n- ".join(faltantes)
            )

        self.stdout.write(
            f"Filas encontradas: {len(df)}"
        )

        # ======================================================
        # PREPARACIÓN Y VALIDACIÓN
        # ======================================================

        registros = []

        skus_vistos = {}
        codigos_vistos = {}

        productos_categoria = {}

        errores = []

        for indice, row in df.iterrows():

            # +2:
            # pandas empieza en 0 y Excel tiene encabezado en fila 1
            fila_excel = indice + 2

            categoria = limpiar_texto(
                row["CATEGORIA_PROVISIONAL"]
            )

            producto = limpiar_texto(
                row["PRODUCTO_FINAL"]
            )

            variante = limpiar_texto(
                row["VARIANTE_FINAL"]
            )

            sku = limpiar_codigo(
                row["SKU_FINAL"]
            )

            codigo_barras = limpiar_codigo(
                row["CODIGO_BARRAS_FINAL"]
            )

            # --------------------------------------------------
            # CAMPOS OBLIGATORIOS
            # --------------------------------------------------

            if not categoria:
                errores.append(
                    f"Fila {fila_excel}: categoría vacía"
                )

            if not producto:
                errores.append(
                    f"Fila {fila_excel}: producto vacío"
                )

            if not variante:
                errores.append(
                    f"Fila {fila_excel}: variante vacía"
                )

            if not sku:
                errores.append(
                    f"Fila {fila_excel}: SKU vacío"
                )

            # --------------------------------------------------
            # LONGITUDES SEGÚN MODELOS DJANGO
            # --------------------------------------------------

            if len(categoria) > 100:
                errores.append(
                    f"Fila {fila_excel}: categoría supera 100 caracteres"
                )

            if len(producto) > 150:
                errores.append(
                    f"Fila {fila_excel}: producto supera 150 caracteres"
                )

            if len(variante) > 150:
                errores.append(
                    f"Fila {fila_excel}: variante supera 150 caracteres"
                )

            if len(sku) > 100:
                errores.append(
                    f"Fila {fila_excel}: SKU supera 100 caracteres"
                )

            if len(codigo_barras) > 100:
                errores.append(
                    f"Fila {fila_excel}: código de barras supera 100 caracteres"
                )

            # --------------------------------------------------
            # SKU ÚNICO IGNORANDO MAYÚSCULAS
            # --------------------------------------------------

            sku_key = sku.casefold()

            if sku_key:
                if sku_key in skus_vistos:
                    errores.append(
                        f"SKU duplicado: {sku!r} "
                        f"en filas {skus_vistos[sku_key]} "
                        f"y {fila_excel}"
                    )
                else:
                    skus_vistos[sku_key] = fila_excel

            # --------------------------------------------------
            # CÓDIGO DE BARRAS
            # --------------------------------------------------

            # Vacío es válido.
            if codigo_barras:
                codigo_key = codigo_barras.casefold()

                if codigo_key in codigos_vistos:
                    errores.append(
                        f"Código de barras duplicado: "
                        f"{codigo_barras!r} "
                        f"en filas {codigos_vistos[codigo_key]} "
                        f"y {fila_excel}"
                    )
                else:
                    codigos_vistos[codigo_key] = fila_excel

            # --------------------------------------------------
            # UN MISMO PRODUCTO NO DEBE CAER EN DOS CATEGORÍAS
            # --------------------------------------------------

            producto_key = producto.casefold()
            categoria_key = categoria.casefold()

            if producto_key in productos_categoria:

                categoria_anterior = productos_categoria[
                    producto_key
                ]

                if categoria_anterior != categoria_key:
                    errores.append(
                        f"Fila {fila_excel}: el producto "
                        f"{producto!r} aparece en más de una categoría"
                    )

            else:
                productos_categoria[
                    producto_key
                ] = categoria_key

            # --------------------------------------------------
            # CAMPOS NUMÉRICOS
            # --------------------------------------------------

            try:
                stock = entero_no_negativo(
                    row["STOCK_FINAL"],
                    "STOCK_FINAL",
                    fila_excel,
                )

                stock_minimo = entero_no_negativo(
                    row["STOCK_MINIMO_FINAL"],
                    "STOCK_MINIMO_FINAL",
                    fila_excel,
                )

                costo = decimal_no_negativo(
                    row["COSTO_FINAL"],
                    "COSTO_FINAL",
                    fila_excel,
                )

                precio_menudeo = decimal_no_negativo(
                    row["PRECIO_MENUDEO_FINAL"],
                    "PRECIO_MENUDEO_FINAL",
                    fila_excel,
                )

                precio_mayoreo = decimal_no_negativo(
                    row["PRECIO_MAYOREO_FINAL"],
                    "PRECIO_MAYOREO_FINAL",
                    fila_excel,
                )

            except CommandError as exc:
                errores.append(str(exc))
                continue

            registros.append(
                {
                    "fila_excel": fila_excel,
                    "categoria": categoria,
                    "producto": producto,
                    "variante": variante,
                    "sku": sku,
                    "codigo_barras": (
                        codigo_barras
                        if codigo_barras
                        else None
                    ),
                    "stock": stock,
                    "stock_minimo": stock_minimo,
                    "costo": costo,
                    "precio_menudeo": precio_menudeo,
                    "precio_mayoreo": precio_mayoreo,
                }
            )

        # ======================================================
        # MOSTRAR ERRORES
        # ======================================================

        if errores:
            self.stdout.write("")
            self.stdout.write(
                self.style.ERROR(
                    f"Se encontraron {len(errores)} errores:"
                )
            )

            for error in errores:
                self.stdout.write(
                    self.style.ERROR(
                        f"  - {error}"
                    )
                )

            raise CommandError(
                "El catálogo NO pasó la validación."
            )

        # ======================================================
        # ESTADÍSTICAS
        # ======================================================

        categorias_unicas = {
            r["categoria"].casefold()
            for r in registros
        }

        productos_unicos = {
            r["producto"].casefold()
            for r in registros
        }

        codigos_validos = sum(
            1
            for r in registros
            if r["codigo_barras"]
        )

        codigos_vacios = (
            len(registros) - codigos_validos
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "VALIDACIÓN CORRECTA"
            )
        )

        self.stdout.write(
            f"Categorías únicas:        {len(categorias_unicas)}"
        )

        self.stdout.write(
            f"Productos únicos:         {len(productos_unicos)}"
        )

        self.stdout.write(
            f"Variantes / SKUs:         {len(registros)}"
        )

        self.stdout.write(
            f"Con código de barras:     {codigos_validos}"
        )

        self.stdout.write(
            f"Sin código de barras:     {codigos_vacios}"
        )

        # ======================================================
        # DRY RUN
        # ======================================================

        if dry_run:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    "DRY RUN: no se realizó ningún cambio "
                    "en la base de datos."
                )
            )

            return

        # ======================================================
        # IMPORTACIÓN REAL
        # ======================================================

        creadas_categorias = 0
        creados_productos = 0
        creadas_variantes = 0
        actualizadas_variantes = 0

        categorias_cache = {}
        productos_cache = {}

        with transaction.atomic():

            for registro in registros:

                # ==============================================
                # CATEGORÍA
                # ==============================================

                categoria_key = registro[
                    "categoria"
                ].casefold()

                categoria = categorias_cache.get(
                    categoria_key
                )

                if categoria is None:

                    categoria = Categoria.objects.filter(
                        nombre__iexact=registro["categoria"]
                    ).first()

                    if categoria is None:
                        categoria = Categoria.objects.create(
                            nombre=registro["categoria"],
                            activo=True,
                        )

                        creadas_categorias += 1

                    categorias_cache[
                        categoria_key
                    ] = categoria

                # ==============================================
                # PRODUCTO
                # ==============================================

                producto_key = registro[
                    "producto"
                ].casefold()

                producto = productos_cache.get(
                    producto_key
                )

                if producto is None:

                    producto = Producto.objects.filter(
                        nombre__iexact=registro["producto"]
                    ).first()

                    if producto is None:
                        producto = Producto.objects.create(
                            categoria=categoria,
                            nombre=registro["producto"],
                            activo=True,
                        )

                        creados_productos += 1

                    else:
                        if producto.categoria_id != categoria.id:
                            raise CommandError(
                                f"El producto "
                                f"{registro['producto']!r} ya existe "
                                f"en otra categoría."
                            )

                    productos_cache[
                        producto_key
                    ] = producto

                # ==============================================
                # VARIANTE
                # ==============================================

                variante = Variante.objects.filter(
                    sku__iexact=registro["sku"]
                ).first()

                datos_variante = {
                    "producto": producto,
                    "nombre": registro["variante"],
                    "codigo_barras": registro[
                        "codigo_barras"
                    ],
                    "stock": registro["stock"],
                    "stock_minimo": registro[
                        "stock_minimo"
                    ],
                    "costo": registro["costo"],
                    "precio_menudeo": registro[
                        "precio_menudeo"
                    ],
                    "precio_mayoreo": registro[
                        "precio_mayoreo"
                    ],
                    "activo": True,
                }

                if variante is None:

                    Variante.objects.create(
                        sku=registro["sku"],
                        stock_defectuoso=0,
                        **datos_variante,
                    )

                    creadas_variantes += 1

                else:

                    for campo, valor in datos_variante.items():
                        setattr(
                            variante,
                            campo,
                            valor,
                        )

                    variante.save()

                    actualizadas_variantes += 1

        # ======================================================
        # RESULTADO
        # ======================================================

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "IMPORTACIÓN COMPLETADA"
            )
        )

        self.stdout.write(
            f"Categorías creadas:       {creadas_categorias}"
        )

        self.stdout.write(
            f"Productos creados:        {creados_productos}"
        )

        self.stdout.write(
            f"Variantes creadas:        {creadas_variantes}"
        )

        self.stdout.write(
            f"Variantes actualizadas:   {actualizadas_variantes}"
        )