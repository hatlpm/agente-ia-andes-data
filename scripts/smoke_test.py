"""Prueba de humo (smoke test) de la conexion con Google Gemini.

PUNTO DE CONTROL del plan: valida la API key y descubre automaticamente que
modelos funcionan de verdad con esta cuenta, antes de construir el agente.

No asume nombres de modelo: los nombres de Gemini cambian con el tiempo y
Google retira modelos para cuentas nuevas (p. ej. gemini-2.5-flash devuelve
404 "no longer available to new users"). Este script prueba una lista de
candidatos y se queda con el primero que responda.

Verifica tres cosas imprescindibles para el proyecto:
  1. Que el LLM responde.
  2. Que el LLM soporta TOOL CALLING (sin esto no hay agente, solo un chatbot).
  3. Que el modelo de embeddings responde (sin esto no hay busqueda semantica).

Uso:
    .venv\\Scripts\\python.exe scripts\\smoke_test.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()

if not API_KEY or API_KEY.startswith("pega_aqui"):
    print("[ERROR] No se encontro GOOGLE_API_KEY.")
    print("        Crea un archivo .env en la raiz del proyecto con esta linea:")
    print("        GOOGLE_API_KEY=tu_clave_real")
    print("        Consigue una clave gratis en https://aistudio.google.com")
    sys.exit(1)

print(f"[OK] API key detectada (termina en ...{API_KEY[-4:]})\n")

# Candidatos ordenados por preferencia: rapidos, economicos y estables primero.
CANDIDATOS_LLM = [
    "gemini-flash-latest",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.5-flash-lite",
]

CANDIDATOS_EMBEDDING = [
    "models/gemini-embedding-001",
    "models/gemini-embedding-2",
]

# ---------------------------------------------------------------------------
# 1. Buscar un modelo de chat que ademas sepa usar herramientas
# ---------------------------------------------------------------------------
print("=" * 70)
print("1. BUSCANDO UN MODELO DE CHAT CON SOPORTE DE HERRAMIENTAS")
print("=" * 70)

from langchain_core.tools import tool  # noqa: E402
from langchain_google_genai import ChatGoogleGenerativeAI  # noqa: E402


@tool
def sumar(a: int, b: int) -> int:
    """Suma dos numeros enteros y devuelve el resultado."""
    return a + b


llm_elegido: str | None = None

for nombre in CANDIDATOS_LLM:
    try:
        llm = ChatGoogleGenerativeAI(
            model=nombre, google_api_key=API_KEY, temperature=0
        )
        # Prueba A: responde texto plano.
        llm.invoke("Responde unicamente con la palabra: FUNCIONA")

        # Prueba B: sabe pedir la ejecucion de una herramienta.
        respuesta = llm.bind_tools([sumar]).invoke(
            "Cuanto es 17 mas 25? Usa la herramienta disponible."
        )
        if not respuesta.tool_calls:
            print(f"   [--] {nombre}: responde, pero NO pidio usar la herramienta")
            continue

        print(f"   [OK] {nombre}: responde y usa herramientas -> {respuesta.tool_calls[0]['args']}")
        llm_elegido = nombre
        break
    except Exception as exc:  # noqa: BLE001 - queremos seguir probando candidatos
        print(f"   [XX] {nombre}: {type(exc).__name__} - {str(exc)[:110]}")

if llm_elegido is None:
    print("\n[ERROR] Ningun modelo de chat funciono. Revisa la API key o la cuota.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 2. Buscar un modelo de embeddings que funcione
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("2. BUSCANDO UN MODELO DE EMBEDDINGS")
print("=" * 70)

from langchain_google_genai import GoogleGenerativeAIEmbeddings  # noqa: E402

embedding_elegido: str | None = None
dimension = 0

for nombre in CANDIDATOS_EMBEDDING:
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model=nombre, google_api_key=API_KEY)
        vector = embeddings.embed_query("politica de vacaciones de la empresa")
        dimension = len(vector)
        print(f"   [OK] {nombre}: vector de dimension {dimension}")
        embedding_elegido = nombre
        break
    except Exception as exc:  # noqa: BLE001
        print(f"   [XX] {nombre}: {type(exc).__name__} - {str(exc)[:110]}")

if embedding_elegido is None:
    print("\n[ERROR] Ningun modelo de embeddings funciono.")
    sys.exit(1)

# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("RESULTADO: conexion validada. Configuracion a usar en src/config.py:")
print("=" * 70)
print(f"   MODELO_LLM       = {llm_elegido!r}")
print(f"   MODELO_EMBEDDING = {embedding_elegido!r}   (dimension {dimension})")
print("=" * 70)
