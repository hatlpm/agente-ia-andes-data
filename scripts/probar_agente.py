"""Bateria de pruebas de aceptacion del agente.

Cada caso comprueba dos cosas distintas:
  1. Que el agente responde correctamente.
  2. Que llego a la respuesta usando la herramienta ADECUADA. Acertar con la
     herramienta equivocada seria casualidad, no un agente que razona.

El ultimo caso es una pregunta trampa: la respuesta no esta en ninguna fuente y
el agente debe admitirlo en lugar de inventarsela.

Uso:
    .venv\\Scripts\\python.exe scripts\\probar_agente.py
"""

import sys

from src.agent import crear_agente, responder

# (pregunta, herramienta esperada, texto que debe aparecer en la respuesta)
CASOS = [
    ("¿Cuantos dias de vacaciones me corresponden al ano?", "buscar_politicas", "30"),
    ("¿Cual es la politica de trabajo remoto?", "buscar_politicas", "3"),
    ("¿Cual es el tope de reembolso por viaticos?", "buscar_politicas", "180"),
    ("¿Cual fue el producto mas vendido en diciembre de 2024?", "consultar_ventas", None),
    ("¿Cuanto facturamos en total durante 2024?", "consultar_ventas", None),
    ("¿Que region tuvo mejor desempeno en ventas?", "consultar_ventas", "Lima"),
    ("¿Cual es el color favorito del gerente?", None, None),
]


def main() -> int:
    agente = crear_agente()
    aprobados = 0

    for numero, (pregunta, herramienta_esperada, texto_esperado) in enumerate(CASOS, start=1):
        print("=" * 78)
        print(f"CASO {numero}: {pregunta}")
        print("=" * 78)

        salida = responder(agente, pregunta)
        usadas = salida["herramientas"]

        print(salida["respuesta"])
        print(f"\n[herramientas usadas: {usadas or 'ninguna'}]")

        if herramienta_esperada is None:
            # Pregunta trampa: lo importante es que reconozca que no lo sabe.
            senales = ["no encuentro", "no dispongo", "no tengo", "no esta", "no puedo"]
            correcto = any(s in salida["respuesta"].lower() for s in senales)
            veredicto = "OK (admitio no saberlo)" if correcto else "FALLO (invento una respuesta)"
        else:
            correcto = herramienta_esperada in usadas
            if correcto and texto_esperado:
                correcto = texto_esperado.lower() in salida["respuesta"].lower()
            veredicto = "OK" if correcto else f"FALLO (esperaba {herramienta_esperada})"

        aprobados += int(correcto)
        print(f"[resultado: {veredicto}]\n")

    print("=" * 78)
    print(f"RESULTADO FINAL: {aprobados}/{len(CASOS)} casos aprobados")
    print("Criterio de aceptacion del plan: al menos 6 de 7.")
    print("=" * 78)

    return 0 if aprobados >= 6 else 1


if __name__ == "__main__":
    sys.exit(main())
