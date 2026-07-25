"""Interfaz web del agente (Streamlit).

Capa de presentacion unicamente: no contiene logica del agente. Todo lo que
sabe hacer esta en `src/`. Asi la misma logica sirve para la web, para la
terminal (`python -m src.agent`) o para un futuro despliegue en la nube.
"""

import streamlit as st

from src import config, uso
from src.agent import crear_agente, responder

st.set_page_config(page_title="Agente Andes Data", page_icon="🔎", layout="centered")

PREGUNTAS_EJEMPLO = [
    "¿Cuántos días de vacaciones me corresponden al año?",
    "¿Cuál es la política de trabajo remoto?",
    "¿Cuál es el tope de reembolso por viáticos?",
    "¿Cuál fue el producto más vendido en diciembre de 2024?",
    "¿Cuánto facturamos en total durante 2024?",
    "¿Qué región tuvo mejor desempeño en ventas?",
]


def pintar_consumo(panel) -> None:
    """Muestra el consumo acumulado del dia en el panel indicado."""
    datos = uso.consumo_hoy()
    total_tokens = datos["tokens_entrada"] + datos["tokens_salida"]
    with panel.container():
        izquierda, derecha = st.columns(2)
        izquierda.metric("Peticiones hoy", datos["peticiones"])
        derecha.metric("Tokens hoy", f"{total_tokens:,}".replace(",", " "))


@st.cache_resource(show_spinner="Cargando el agente y los documentos...")
def obtener_agente():
    """Se construye una sola vez por sesion del servidor.

    Streamlit vuelve a ejecutar todo el script en cada interaccion; sin esta
    cache se recargarian el indice vectorial y el CSV en cada pregunta.
    """
    return crear_agente()


st.title("🔎 Agente de documentos internos")
st.caption("Andes Data S.A.C. — pregunta en lenguaje natural sobre las políticas internas y el histórico de ventas.")

with st.sidebar:
    st.header("Cómo funciona")
    st.markdown(
        """
El agente tiene **dos herramientas** y decide sola cuál usar:

- 📄 **Manual de políticas** (PDF) — búsqueda semántica (RAG) para normas y beneficios.
- 📊 **Histórico de ventas** (CSV) — ejecuta pandas para calcular cifras reales.

Si la respuesta no está en ninguna de las dos fuentes, lo dice en lugar de inventarla.
        """
    )
    st.divider()
    st.subheader("Preguntas de ejemplo")
    for pregunta in PREGUNTAS_EJEMPLO:
        st.markdown(f"- {pregunta}")
    st.divider()
    st.subheader("Consumo de la API")
    panel_consumo = st.empty()
    st.caption(
        f"Modelo: `{config.MODELO_LLM}`. Cada pregunta consume entre 2 y 3 peticiones."
    )
    st.caption(
        "⚠️ Contador **local de esta aplicación**, no el saldo real de la cuenta: "
        "la API de Gemini no expone la cuota restante. "
        "Consúltala en [ai.dev/rate-limit](https://ai.dev/rate-limit)."
    )

    st.divider()
    if st.button("Limpiar conversación", use_container_width=True):
        st.session_state.mensajes = []
        st.rerun()

pintar_consumo(panel_consumo)

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# El agente se crea aqui para poder mostrar un error legible si falta la API key
# o los documentos, en vez de una traza de Python en pantalla.
try:
    agente = obtener_agente()
except Exception as exc:  # noqa: BLE001
    st.error(f"No se pudo iniciar el agente:\n\n{exc}")
    st.stop()

for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])
        if mensaje.get("herramientas"):
            st.caption(f"🔧 Herramientas usadas: {', '.join(mensaje['herramientas'])}")

if pregunta := st.chat_input("Escribe tu pregunta..."):
    st.session_state.mensajes.append({"role": "user", "content": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    with st.chat_message("assistant"):
        with st.spinner("Consultando los documentos..."):
            consumo = None
            try:
                # Se envia el historial previo (sin el turno actual) para que el
                # agente entienda preguntas de seguimiento como "¿y en 2023?".
                salida = responder(agente, pregunta, st.session_state.mensajes[:-1])
                texto = salida["respuesta"]
                herramientas = sorted(set(salida["herramientas"]))
                consumo = salida["consumo"]
            except Exception as exc:  # noqa: BLE001
                herramientas = []
                if "RESOURCE_EXHAUSTED" in str(exc) or "429" in str(exc):
                    # Caso frecuente y esperable en la capa gratuita: merece una
                    # explicacion accionable en vez de una traza de Python.
                    texto = (
                        "**Se agotó la cuota gratuita diaria de este modelo.**\n\n"
                        "No es un fallo de la aplicación: la capa gratuita de Gemini limita "
                        "las peticiones por día y por modelo, y se renueva cada día.\n\n"
                        "Para continuar ahora mismo, ejecuta `python scripts/smoke_test.py`, "
                        "que indica qué modelo sigue disponible, y añádelo al archivo `.env` "
                        "como `MODELO_LLM=<el modelo que funcione>`."
                    )
                else:
                    texto = f"Ocurrió un error al responder: {exc}"

        st.markdown(texto)
        if herramientas:
            st.caption(f"🔧 Herramientas usadas: {', '.join(herramientas)}")
        if consumo:
            st.caption(
                f"📊 Esta respuesta: {consumo['peticiones']} peticiones · "
                f"{consumo['tokens_entrada'] + consumo['tokens_salida']} tokens"
            )

    st.session_state.mensajes.append(
        {"role": "assistant", "content": texto, "herramientas": herramientas}
    )
    pintar_consumo(panel_consumo)
