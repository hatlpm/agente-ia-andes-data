"""Contador local del consumo de la API de Gemini.

IMPORTANTE — lo que este modulo es y lo que no es:

  SI es: un registro propio de lo que ESTA aplicacion ha gastado, acumulado por
         dia en un archivo local, que sobrevive a los reinicios.

  NO es: el saldo real de la cuenta. La API de Gemini no expone ningun endpoint
         para consultar la cuota restante. El unico dato oficial esta en el
         panel web https://ai.dev/rate-limit. Si se hacen llamadas con la misma
         clave desde otro programa, este contador no las vera.

Sirve para lo que importa en la practica: saber cuanto lleva consumido la sesion
y anticipar el error 429 antes de que aparezca en medio de una demostracion.
"""

import json
from datetime import date

from src import config

RUTA_REGISTRO = config.RAIZ / ".uso_api.json"

# Una pregunta consume normalmente 2 llamadas (decidir la herramienta y redactar
# la respuesta con su resultado) y hasta 3 si el agente encadena dos consultas.
PETICIONES_POR_PREGUNTA = 2


def _leer() -> dict:
    if not RUTA_REGISTRO.exists():
        return {}
    try:
        return json.loads(RUTA_REGISTRO.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # Un registro corrupto no debe impedir que el agente funcione.
        return {}


def registrar(peticiones: int, tokens_entrada: int, tokens_salida: int) -> None:
    """Suma el consumo de una interaccion al acumulado de hoy."""
    datos = _leer()
    hoy = date.today().isoformat()
    acumulado = datos.get(hoy, {"peticiones": 0, "tokens_entrada": 0, "tokens_salida": 0})

    acumulado["peticiones"] += peticiones
    acumulado["tokens_entrada"] += tokens_entrada
    acumulado["tokens_salida"] += tokens_salida
    datos[hoy] = acumulado

    # Se conservan solo los ultimos 30 dias para que el archivo no crezca.
    for dia in sorted(datos.keys())[:-30]:
        del datos[dia]

    try:
        RUTA_REGISTRO.write_text(json.dumps(datos, indent=2), encoding="utf-8")
    except OSError:
        pass  # Registrar el consumo nunca debe romper una respuesta.


def consumo_hoy() -> dict:
    """Devuelve el consumo acumulado del dia actual."""
    return _leer().get(
        date.today().isoformat(),
        {"peticiones": 0, "tokens_entrada": 0, "tokens_salida": 0},
    )
