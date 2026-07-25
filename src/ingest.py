"""Fase OFFLINE del RAG: convertir el PDF en un indice vectorial buscable.

El flujo es siempre el mismo:

    PDF  ->  texto por pagina  ->  fragmentos (chunks)  ->  vectores  ->  FAISS

Se ejecuta una sola vez y el resultado queda guardado en disco. Asi la
aplicacion arranca al instante y no vuelve a gastar cuota de API generando
embeddings que ya calculo antes.

Uso:
    .venv\\Scripts\\python.exe -m src.ingest
"""

from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src import config

# La API de embeddings limita cuantos textos acepta por peticion; enviamos
# tandas pequenas para no chocar con ese limite en documentos grandes.
TAMANO_LOTE = 50


def obtener_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Crea el objeto que convierte texto en vectores."""
    return GoogleGenerativeAIEmbeddings(
        model=config.MODELO_EMBEDDING,
        google_api_key=config.GOOGLE_API_KEY,
    )


def cargar_y_fragmentar() -> list[Document]:
    """Lee el PDF y lo parte en fragmentos manejables.

    PyPDFLoader devuelve un documento por pagina y guarda el numero de pagina en
    los metadatos, lo que despues permite citar la fuente de cada respuesta.
    """
    paginas = PyPDFLoader(str(config.RUTA_PDF)).load()

    divisor = RecursiveCharacterTextSplitter(
        chunk_size=config.TAMANO_CHUNK,
        chunk_overlap=config.SOLAPAMIENTO_CHUNK,
        # Se intenta cortar primero por parrafo, luego por linea, luego por
        # frase y solo en ultimo caso por palabra: asi los fragmentos conservan
        # unidades de significado completas.
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    fragmentos = divisor.split_documents(paginas)

    # La numeracion de pypdf empieza en 0; la pasamos a numeracion humana.
    for fragmento in fragmentos:
        pagina = fragmento.metadata.get("page", 0)
        fragmento.metadata["pagina"] = int(pagina) + 1

    return fragmentos


def construir_indice() -> FAISS:
    """Genera el indice vectorial desde cero y lo guarda en disco."""
    config.validar_configuracion()

    fragmentos = cargar_y_fragmentar()
    print(f"[ingest] {len(fragmentos)} fragmentos extraidos de {config.RUTA_PDF.name}")

    embeddings = obtener_embeddings()

    # Se crea el indice con el primer lote y se van agregando los siguientes.
    primer_lote = fragmentos[:TAMANO_LOTE]
    indice = FAISS.from_documents(primer_lote, embeddings)
    print(f"[ingest] lote 1: {len(primer_lote)} fragmentos vectorizados")

    for numero, inicio in enumerate(range(TAMANO_LOTE, len(fragmentos), TAMANO_LOTE), start=2):
        lote = fragmentos[inicio : inicio + TAMANO_LOTE]
        indice.add_documents(lote)
        print(f"[ingest] lote {numero}: {len(lote)} fragmentos vectorizados")

    config.RUTA_VECTORSTORE.mkdir(parents=True, exist_ok=True)
    indice.save_local(str(config.RUTA_VECTORSTORE))
    print(f"[ingest] indice guardado en {config.RUTA_VECTORSTORE}")

    return indice


def cargar_indice() -> FAISS:
    """Devuelve el indice listo para consultar.

    Si todavia no existe en disco, lo construye. De este modo la aplicacion
    nunca falla en el primer arranque por no haber corrido la ingesta a mano.
    """
    config.validar_configuracion()

    if not (config.RUTA_VECTORSTORE / "index.faiss").exists():
        print("[ingest] no hay indice guardado; construyendolo por primera vez...")
        return construir_indice()

    return FAISS.load_local(
        str(config.RUTA_VECTORSTORE),
        obtener_embeddings(),
        # El formato de FAISS usa pickle al deserializar. Lo permitimos porque
        # el archivo lo genera este mismo proyecto en la maquina local.
        allow_dangerous_deserialization=True,
    )


if __name__ == "__main__":
    indice = construir_indice()

    print("\n--- Prueba rapida de recuperacion ---")
    for consulta in ["dias de vacaciones", "trabajo remoto", "tope de viaticos"]:
        resultados = indice.similarity_search(consulta, k=1)
        extracto = resultados[0].page_content[:160].replace("\n", " ")
        print(f"\n[{consulta}] (pagina {resultados[0].metadata['pagina']})")
        print(f"  {extracto}...")
