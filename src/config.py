"""Configuracion central del proyecto.

Un unico lugar donde viven las rutas, los nombres de modelo y la API key, para
que ningun otro modulo tenga que saber donde esta el archivo .env ni como se
llama el modelo. Si manana cambiamos de modelo, se cambia aqui y nada mas.

Los nombres de modelo por defecto NO son inventados: son los que valido el
script `scripts/smoke_test.py` contra la cuenta real.
"""

from pathlib import Path

from dotenv import load_dotenv
import os

# Raiz del proyecto: dos niveles arriba de este archivo (src/config.py -> src -> raiz).
RAIZ = Path(__file__).resolve().parent.parent

load_dotenv(RAIZ / ".env")

# --- Credenciales ----------------------------------------------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()

# --- Modelos ---------------------------------------------------------------
# Se prefiere un modelo "lite" por su cuota gratuita: los modelos de ultima
# generacion tienen cupos diarios muy bajos (gemini-flash-latest, que resuelve
# al flash mas reciente, permite solo 20 peticiones al dia en la capa gratuita,
# y una sola pregunta consume entre 2 y 3).
#
# Si esta cuota tambien se agota, ejecuta `python scripts/smoke_test.py`: prueba
# varios candidatos y dice cual responde. Luego basta con anadir la linea
# MODELO_LLM=<el que funcione> al archivo .env, sin tocar el codigo.
MODELO_LLM = os.getenv("MODELO_LLM", "gemini-flash-lite-latest")
MODELO_EMBEDDING = os.getenv("MODELO_EMBEDDING", "models/gemini-embedding-001")

# --- Rutas de datos --------------------------------------------------------
RUTA_PDF = RAIZ / "data" / "politicas_internas.pdf"
RUTA_CSV = RAIZ / "data" / "ventas.csv"
RUTA_VECTORSTORE = RAIZ / "vectorstore"

# --- Parametros del RAG ----------------------------------------------------
# 1000 caracteres es un tamano que suele contener una seccion completa de una
# politica; el solapamiento de 150 evita partir una frase justo en el limite y
# perder el contexto en los bordes del fragmento.
TAMANO_CHUNK = 1000
SOLAPAMIENTO_CHUNK = 150

# Cuantos fragmentos se recuperan por consulta. Cuatro da contexto suficiente
# sin saturar el prompt ni la cuota gratuita.
FRAGMENTOS_A_RECUPERAR = 4


def validar_configuracion() -> None:
    """Falla temprano y con un mensaje util si algo esencial no esta listo."""
    if not GOOGLE_API_KEY or GOOGLE_API_KEY.startswith("pega_aqui"):
        raise RuntimeError(
            "Falta GOOGLE_API_KEY. Crea un archivo .env en la raiz del proyecto "
            "con la linea: GOOGLE_API_KEY=tu_clave. "
            "Consigue una clave gratis en https://aistudio.google.com"
        )
    if not RUTA_PDF.exists():
        raise RuntimeError(
            f"No se encontro el PDF en {RUTA_PDF}. "
            "Generalo con: python scripts/generar_datos.py"
        )
    if not RUTA_CSV.exists():
        raise RuntimeError(
            f"No se encontro el CSV en {RUTA_CSV}. "
            "Generalo con: python scripts/generar_datos.py"
        )
