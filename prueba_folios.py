import concurrent.futures
import os

import requests
from dotenv import load_dotenv


load_dotenv()

URL = "http://127.0.0.1:8000/api/ventas/"

TOKEN = os.getenv("PRUEBA_FOLIOS_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "PRUEBA_FOLIOS_TOKEN no está configurado. "
        "Define esta variable de entorno antes de ejecutar el script."
    )

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

DATA = {
    "caja_id": "af530a55-0da3-42e1-bcd3-ff1c393a71c4",
    "metodo_pago_id": "e8906973-9c11-4395-af25-402ea78de074",
    "productos": [
        {
            "variante_id": "b9db3ec6-fbb4-48d1-b789-b89fce592a9c",
            "cantidad": 1,
        }
    ],
    "descuento": "0.00",
}


def crear_venta(numero):
    try:
        response = requests.post(
            URL,
            json=DATA,
            headers=HEADERS,
            timeout=30,
        )

        print(f"\n========== RESPUESTA {numero} ==========")
        print("Status:", response.status_code)
        print("Body:", response.text)

    except requests.RequestException as e:
        print(f"\nError en petición {numero}: {e}")


with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:

    futuros = [
        executor.submit(crear_venta, 1),
        executor.submit(crear_venta, 2),
    ]

    for futuro in futuros:
        futuro.result()
