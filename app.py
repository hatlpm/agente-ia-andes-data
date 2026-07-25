"""Interfaz web del agente (Streamlit).

Capa de presentacion unicamente: no contiene logica del agente. Todo lo que
sabe hacer esta en `src/`. Asi la misma logica sirve para la web, para la
terminal (`python -m src.agent`) o para un futuro despliegue en la nube.
"""

import streamlit as st

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
    if st.button("Limpiar conversación", use_container_width=True):
        st.session_state.mensajes = []
        st.rerun()

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
            try:
                # Se envia el historial previo (sin el turno actual) para que el
                # agente entienda preguntas de seguimiento como "¿y en 2023?".
                salida = responder(agente, pregunta, st.session_state.mensajes[:-1])
                texto = salida["respuesta"]
                herramientas = sorted(set(salida["herramientas"]))
            except Exception as exc:  # noqa: BLE001
                texto = f"Ocurrió un error al responder: {exc}"
                herramientas = []

        st.markdown(texto)
        if herramientas:
            st.caption(f"🔧 Herramientas usadas: {', '.join(herramientas)}")

    st.session_state.mensajes.append(
        {"role": "assistant", "content": texto, "herramientas": herramientas}
    )
