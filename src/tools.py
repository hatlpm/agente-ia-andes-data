"""Las dos herramientas que el agente puede decidir usar.

La idea central del proyecto: son dos fuentes de naturaleza distinta y cada una
exige una tecnica distinta.

  - El PDF es texto libre  -> busqueda semantica (RAG). No se puede "calcular"
    sobre el, solo encontrar los pasajes relevantes.
  - El CSV es tabular      -> hace falta CALCULAR (sumar, agrupar, ordenar).
    Buscar "fragmentos parecidos" no responderia "cuanto facturamos en 2024".

El agente lee la descripcion de cada herramienta y elige. Esa eleccion es lo
que lo convierte en un agente y no en un simple chatbot con documentos.
"""

import ast
import builtins
import io

import pandas as pd
from langchain_core.tools import tool

from src import config
from src.ingest import cargar_indice

# Recursos caros (indice vectorial y DataFrame) cargados una sola vez y
# reutilizados en cada llamada. Sin esto, cada pregunta releeria todo el disco.
_indice = None
_df: pd.DataFrame | None = None

# Limite de caracteres devueltos al modelo: evita inundar el prompt (y gastar
# cuota) si el agente pide accidentalmente la tabla entera.
LIMITE_RESPUESTA = 3000

# --- Contencion de la ejecucion de codigo -----------------------------------
#
# `consultar_ventas` ejecuta codigo escrito por el modelo. Con la aplicacion
# publicada en internet, cualquiera puede intentar un "prompt injection" para
# que ese codigo haga algo distinto de consultar el DataFrame. Dos barreras:
#
#   1. Lista blanca de builtins. Python inyecta todos los builtins por defecto
#      al ejecutar codigo, incluidos __import__, open, eval y exec. Aqui solo
#      se exponen los que una consulta pandas legitima puede necesitar.
#   2. Prohibicion de atributos "dunder". La via de escape clasica de estos
#      sandboxes no es importar nada, sino recorrer la jerarquia de clases
#      (().__class__.__bases__[0].__subclasses__()) hasta alcanzar algo util.
#      Sin dobles guiones bajos, ese camino queda cortado.
#
# No convierte esto en un sandbox real (para eso haria falta aislar el proceso
# o el contenedor), pero eleva mucho el coste de un abuso.
BUILTINS_PERMITIDOS = {
    nombre: getattr(builtins, nombre)
    for nombre in (
        "abs", "all", "any", "bool", "dict", "divmod", "enumerate", "filter",
        "float", "format", "int", "len", "list", "map", "max", "min", "pow",
        "range", "reversed", "round", "set", "slice", "sorted", "str", "sum",
        "tuple", "zip",
    )
}


def _obtener_indice():
    global _indice
    if _indice is None:
        _indice = cargar_indice()
    return _indice


def _obtener_df() -> pd.DataFrame:
    global _df
    if _df is None:
        _df = pd.read_csv(config.RUTA_CSV)
    return _df


def _ejecutar_codigo(codigo: str, entorno: dict) -> object:
    """Ejecuta el codigo y devuelve el valor de su ultima expresion.

    Replica el comportamiento de una consola interactiva de Python: si la ultima
    linea es una expresion (por ejemplo `df.monto_total.sum()`), su valor es el
    resultado. Asi el modelo puede escribir codigo natural sin tener que acordarse
    de asignar a una variable concreta ni de usar print().
    """
    arbol = ast.parse(codigo)

    if arbol.body and isinstance(arbol.body[-1], ast.Expr):
        previas = ast.Module(body=arbol.body[:-1], type_ignores=[])
        exec(compile(previas, "<agente>", "exec"), entorno)  # noqa: S102
        ultima = ast.Expression(body=arbol.body[-1].value)
        return eval(compile(ultima, "<agente>", "eval"), entorno)  # noqa: S307

    exec(compile(arbol, "<agente>", "exec"), entorno)  # noqa: S102
    return entorno.get("resultado")


def _formatear(valor: object) -> str:
    """Convierte cualquier resultado de pandas en texto legible para el modelo."""
    if valor is None:
        return "El codigo se ejecuto pero no produjo ningun resultado visible."

    if isinstance(valor, pd.DataFrame):
        if valor.empty:
            return "La consulta no devolvio ninguna fila."
        buffer = io.StringIO()
        valor.head(30).to_string(buffer)
        texto = buffer.getvalue()
        if len(valor) > 30:
            texto += f"\n\n[mostrando 30 de {len(valor)} filas]"
    elif isinstance(valor, pd.Series):
        texto = valor.head(30).to_string()
    else:
        texto = str(valor)

    return texto[:LIMITE_RESPUESTA]


@tool
def buscar_politicas(consulta: str) -> str:
    """Busca informacion en el manual de politicas internas de Andes Data S.A.C.

    Usa esta herramienta para preguntas sobre normas, reglas, beneficios y
    procedimientos de la empresa: vacaciones, trabajo remoto e hibrido, horarios,
    licencias y permisos, viaticos y reembolsos, seguridad de la informacion,
    codigo de conducta, capacitacion, evaluacion de desempeno, beneficios
    corporativos y canal de denuncias.

    NO la uses para preguntas sobre cifras de ventas, facturacion, productos
    vendidos, clientes o regiones comerciales: para eso existe consultar_ventas.

    Args:
        consulta: la pregunta o el tema a buscar, en lenguaje natural.

    Returns:
        Los fragmentos mas relevantes del manual, cada uno con su numero de pagina.
    """
    documentos = _obtener_indice().similarity_search(
        consulta, k=config.FRAGMENTOS_A_RECUPERAR
    )

    if not documentos:
        return "No se encontro ningun fragmento relevante en el manual de politicas."

    partes = [
        f"--- Fragmento {i} (pagina {doc.metadata.get('pagina', '?')}) ---\n{doc.page_content}"
        for i, doc in enumerate(documentos, start=1)
    ]
    return "\n\n".join(partes)


@tool
def consultar_ventas(codigo_python: str) -> str:
    """Ejecuta codigo pandas sobre el historico de ventas y devuelve el resultado.

    Usa esta herramienta para CUALQUIER pregunta que requiera calcular sobre los
    datos de ventas: totales, promedios, rankings, conteos, comparaciones entre
    periodos, mejor producto, mejor region, mejor vendedor, etc.

    Escribe codigo Python de una sola expresion final cuyo valor sea la respuesta.
    El DataFrame ya esta cargado en la variable `df` y `pd` es pandas.
    NO uses print(), NO leas el archivo, NO importes nada.

    Esquema de `df` (1200 filas, ventas de 2023-01-01 a 2025-12-29):
        fecha           object  - texto "YYYY-MM-DD". NO es datetime: para filtrar
                                  por periodo usa df.fecha.str.startswith("2024-12")
                                  o convierte con pd.to_datetime(df.fecha).
        region          object  - Lima, Arequipa, Cusco, Trujillo, Piura
        producto        object  - Dashboard Corporativo, Migracion Cloud,
                                  Modelo Predictivo, Auditoria de Datos,
                                  Capacitacion Analytics, Integracion ERP,
                                  Data Warehouse
        categoria       object  - Consultoria, Licencias, Capacitacion
        cliente         object  - 40 empresas distintas
        vendedor        object  - 8 vendedores
        cantidad        int64   - unidades vendidas (1 a 10)
        precio_unitario float64 - precio por unidad en soles
        monto_total     float64 - cantidad * precio_unitario (usa esta para facturacion)

    Ejemplos:
        df[df.fecha.str.startswith("2024-12")].groupby("producto").cantidad.sum().idxmax()
        df[df.fecha.str.startswith("2024")].monto_total.sum()
        df.groupby("region").monto_total.sum().sort_values(ascending=False)

    Args:
        codigo_python: el codigo pandas a ejecutar.

    Returns:
        El resultado del calculo en texto, o el mensaje de error si el codigo fallo.
    """
    # El modelo a veces envuelve el codigo en un bloque markdown; lo limpiamos.
    codigo = codigo_python.strip()
    if codigo.startswith("```"):
        codigo = codigo.split("```")[1]
        if codigo.startswith("python"):
            codigo = codigo[len("python") :]
        codigo = codigo.strip()

    if "__" in codigo:
        return (
            "ERROR: no se permite usar atributos con dobles guiones bajos. "
            "Escribe una consulta pandas normal sobre `df`."
        )

    entorno = {
        "df": _obtener_df(),
        "pd": pd,
        "__builtins__": BUILTINS_PERMITIDOS,
    }

    try:
        return _formatear(_ejecutar_codigo(codigo, entorno))
    except Exception as exc:  # noqa: BLE001
        # El error se devuelve como texto, no se lanza: asi el agente lo lee,
        # corrige su codigo y vuelve a intentar en la siguiente vuelta.
        return (
            f"ERROR al ejecutar el codigo: {type(exc).__name__}: {exc}\n"
            "Revisa los nombres de las columnas y vuelve a intentarlo."
        )


def obtener_herramientas() -> list:
    """Devuelve la lista de herramientas disponibles para el agente."""
    return [buscar_politicas, consultar_ventas]
