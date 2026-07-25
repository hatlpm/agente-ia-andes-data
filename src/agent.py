"""Ensamblado del agente: modelo + herramientas + instrucciones.

Aqui se junta todo. `create_agent` de LangChain construye el bucle del agente:
recibe la pregunta, deja que el modelo decida si necesita una herramienta, la
ejecuta de verdad, le devuelve el resultado al modelo y repite hasta que este
tenga suficiente para responder. Ese bucle es lo que distingue a un agente de
un chatbot: nosotros no decidimos que fuente consultar, lo decide el modelo.
"""

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from src import config
from src.tools import obtener_herramientas

INSTRUCCIONES = """\
Eres el asistente interno de Andes Data S.A.C., una consultora de datos peruana.
Respondes preguntas del personal consultando dos fuentes oficiales de la empresa.

TUS FUENTES Y CUANDO USAR CADA UNA:

1. `buscar_politicas` -> el manual de politicas internas (documento PDF).
   Uselo para normas, reglas, beneficios y procedimientos: vacaciones, trabajo
   remoto, horarios, licencias, viaticos, seguridad de la informacion, codigo de
   conducta, capacitacion, evaluacion de desempeno, beneficios y denuncias.

2. `consultar_ventas` -> el historico de ventas (archivo CSV, 2023-2025).
   Uselo para TODO lo que exija calcular: facturacion, unidades vendidas,
   rankings de productos, regiones, clientes o vendedores, y comparaciones
   entre periodos. Escriba codigo pandas; nunca estime cifras de memoria.

REGLAS DE TRABAJO:

- Elija siempre la herramienta adecuada antes de responder. No responda de
  memoria preguntas que dependan de estas fuentes.
- Si una herramienta devuelve un ERROR, corrija su codigo y vuelva a intentarlo.
- NUNCA invente informacion. Si la respuesta no esta en las fuentes, digalo
  claramente: "No encuentro esa informacion en los documentos disponibles."
  Es preferible admitirlo a dar un dato falso.
- Si la pregunta no tiene relacion con la empresa, explique con amabilidad que
  solo puede responder sobre las politicas internas y las ventas de Andes Data.

FORMATO DE LA RESPUESTA:

- Responda en espanol, de forma directa y concreta. Primero el dato que se pide,
  despues el detalle relevante si aporta.
- Exprese los montos en soles con separador de miles (ejemplo: S/ 1,234,567.89).
- Termine SIEMPRE indicando la fuente en una linea aparte:
    - "Fuente: Manual de politicas internas (pagina N)"
    - "Fuente: Historico de ventas (ventas.csv)"
"""


def crear_agente():
    """Construye el agente listo para responder preguntas."""
    config.validar_configuracion()

    modelo = ChatGoogleGenerativeAI(
        model=config.MODELO_LLM,
        google_api_key=config.GOOGLE_API_KEY,
        # temperatura 0 = respuestas deterministas. En un asistente que cita
        # politicas y cifras no queremos creatividad, queremos exactitud.
        temperature=0,
    )

    return create_agent(
        model=modelo,
        tools=obtener_herramientas(),
        system_prompt=INSTRUCCIONES,
    )


def _extraer_texto(contenido) -> str:
    """Normaliza el contenido de un mensaje a texto plano.

    Los modelos recientes no siempre devuelven una cadena: pueden devolver una
    lista de bloques (texto, razonamiento interno, firmas). Nos quedamos solo
    con los bloques de texto, que es lo que el usuario debe ver.
    """
    if isinstance(contenido, str):
        return contenido

    if isinstance(contenido, list):
        partes = []
        for bloque in contenido:
            if isinstance(bloque, str):
                partes.append(bloque)
            elif isinstance(bloque, dict) and bloque.get("type") == "text":
                partes.append(bloque.get("text", ""))
        return "\n".join(parte for parte in partes if parte).strip()

    return str(contenido)


def responder(agente, pregunta: str, historial: list[dict] | None = None) -> dict:
    """Envia una pregunta al agente y devuelve su respuesta.

    Args:
        agente: el objeto devuelto por `crear_agente()`.
        pregunta: la pregunta del usuario.
        historial: turnos previos, como [{"role": "user"|"assistant", "content": str}].

    Returns:
        {"respuesta": str, "herramientas": list[str]} - el texto final y los
        nombres de las herramientas que el agente decidio usar (util para
        comprobar en las pruebas que enruto bien la pregunta).
    """
    mensajes = []
    for turno in historial or []:
        if turno["role"] == "user":
            mensajes.append(HumanMessage(content=turno["content"]))
        else:
            mensajes.append(AIMessage(content=turno["content"]))
    mensajes.append(HumanMessage(content=pregunta))

    resultado = agente.invoke({"messages": mensajes})

    herramientas_usadas = [
        llamada["name"]
        for mensaje in resultado["messages"]
        for llamada in getattr(mensaje, "tool_calls", []) or []
    ]

    return {
        "respuesta": _extraer_texto(resultado["messages"][-1].content),
        "herramientas": herramientas_usadas,
    }


if __name__ == "__main__":
    agente = crear_agente()
    print("Agente de Andes Data S.A.C. — escribe 'salir' para terminar.\n")

    conversacion: list[dict] = []
    while True:
        try:
            pregunta = input("Tu: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not pregunta or pregunta.lower() in {"salir", "exit", "quit"}:
            break

        salida = responder(agente, pregunta, conversacion)
        print(f"\nAgente: {salida['respuesta']}")
        if salida["herramientas"]:
            print(f"[herramientas usadas: {', '.join(salida['herramientas'])}]")
        print()

        conversacion.append({"role": "user", "content": pregunta})
        conversacion.append({"role": "assistant", "content": salida["respuesta"]})
