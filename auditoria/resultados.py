class ResultadosAuditoria:

    def __init__(self):
        self.pass_count = 0
        self.fail_count = 0
        self.error_count = 0
        self.sin_regla_count = 0
        self.omitido_count = 0
        self.resultados = []

    def pass_test(self, nombre, detalle=""):
        self.pass_count += 1
        self.resultados.append(
            ("PASS", nombre, detalle)
        )

    def fail_test(self, nombre, detalle=""):
        self.fail_count += 1
        self.resultados.append(
            ("FAIL", nombre, detalle)
        )

    def error_test(self, nombre, detalle=""):
        self.error_count += 1
        self.resultados.append(
            ("ERROR", nombre, detalle)
        )

    def sin_regla(self, nombre, detalle=""):
        self.sin_regla_count += 1
        self.resultados.append(
            ("SIN_REGLA", nombre, detalle)
        )

    def omitido(self, nombre, detalle=""):
        self.omitido_count += 1
        self.resultados.append(
            ("OMITIDO", nombre, detalle)
        )

    def imprimir_resumen(self):
        print("\n" + "=" * 60)
        print("              RUBY — MEGA AUDITORÍA")
        print("=" * 60)

        for estado, nombre, detalle in self.resultados:
            print(f"[{estado}] {nombre}")

            if detalle:
                print(f"       {detalle}")

        print("\n" + "=" * 60)
        print("RESULTADO")
        print("=" * 60)

        print(f"PASS      : {self.pass_count}")
        print(f"FAIL      : {self.fail_count}")
        print(f"ERROR     : {self.error_count}")
        print(f"SIN_REGLA : {self.sin_regla_count}")
        print(f"OMITIDO   : {self.omitido_count}")

        print("=" * 60)