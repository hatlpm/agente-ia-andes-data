"""Generador de los documentos internos de Andes Data S.A.C.

Crea los dos archivos que alimentan al agente de IA:

    data/politicas_internas.pdf  -> manual de politicas internas (reportlab)
    data/ventas.csv              -> historico de ventas 2023-2025 (pandas)

Los datos son ficticios pero DETERMINISTAS: se fija la semilla (42) tanto en
`random` como en `numpy.random`, de modo que cada ejecucion reproduce
exactamente el mismo CSV. Eso permite escribir pruebas y documentacion sobre
cifras concretas.

Uso:
    .venv\\Scripts\\python.exe scripts\\generar_datos.py
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

# ---------------------------------------------------------------------------
# Configuracion general
# ---------------------------------------------------------------------------

SEMILLA = 42

RAIZ = Path(__file__).resolve().parent.parent
CARPETA_DATOS = RAIZ / "data"
RUTA_PDF = CARPETA_DATOS / "politicas_internas.pdf"
RUTA_CSV = CARPETA_DATOS / "ventas.csv"


# ===========================================================================
# 1. PDF DE POLITICAS INTERNAS
# ===========================================================================

# Cada seccion es (titulo, [parrafos]). El texto va con tildes correctas: el
# agente hara busqueda semantica sobre este contenido y las preguntas de los
# usuarios vendran escritas en espanol natural. Las cifras son
# intencionadamente especificas (montos, plazos, areas) para que el agente
# pueda citar hechos verificables en lugar de generalidades.
SECCIONES: list[tuple[str, list[str]]] = [
    (
        "1. Objeto y alcance del manual",
        [
            "El presente Manual de Políticas Internas de <b>Andes Data S.A.C.</b> "
            "(en adelante, «la Empresa») establece las reglas de convivencia, los "
            "derechos y los deberes que rigen la relación laboral de todo el "
            "personal. Andes Data S.A.C. es una consultora de datos con domicilio "
            "fiscal en Av. Javier Prado Este 4200, oficina 802, distrito de "
            "Santiago de Surco, Lima, Perú, con RUC 20548921736 y una plantilla "
            "de 148 colaboradores al cierre del ejercicio 2025.",
            "Este manual es de cumplimiento obligatorio para la totalidad de "
            "colaboradores en planilla, practicantes profesionales y "
            "preprofesionales, sin distinción de área, sede o modalidad de "
            "trabajo. Los consultores externos y proveedores se rigen por sus "
            "contratos de servicios, pero deben observar obligatoriamente los "
            "capítulos 7 (Seguridad de la Información) y 8 (Código de Conducta).",
            "La versión vigente es la <b>v4.2, aprobada el 15 de enero de 2025</b> "
            "por el Comité de Gestión Humana y publicada en la intranet "
            "corporativa. Reemplaza íntegramente a la versión 3.8. Cualquier "
            "consulta sobre su interpretación debe dirigirse al área de Gestión "
            "Humana, al correo gestionhumana@andesdata.pe o al anexo 210.",
        ],
    ),
    (
        "2. Horario laboral y flexibilidad",
        [
            "La jornada ordinaria de trabajo es de <b>48 horas semanales</b>, "
            "distribuidas de lunes a viernes de 09:00 a 18:00 horas, con un "
            "refrigerio de 60 minutos que no forma parte de la jornada efectiva. "
            "Los sábados no son laborables, salvo guardia programada del equipo "
            "de Soporte de Plataformas.",
            "La Empresa aplica un esquema de <b>horario flexible de entrada</b>: "
            "el colaborador puede iniciar labores entre las 08:00 y las 10:00 "
            "horas, completando siempre las 9 horas de permanencia diaria. La "
            "franja de <b>11:00 a 16:00 horas se considera horario núcleo</b>, "
            "durante el cual todo el personal debe estar disponible para "
            "reuniones y coordinaciones.",
            "Los viernes se aplica la modalidad de <b>salida anticipada a las "
            "15:00 horas</b>, siempre que se hayan cumplido las horas "
            "comprometidas de lunes a jueves. El trabajo en sobretiempo requiere "
            "autorización escrita previa del jefe de área y se compensa con "
            "descanso equivalente dentro de los 30 días calendario siguientes.",
        ],
    ),
    (
        "3. Política de trabajo remoto",
        [
            "Andes Data S.A.C. opera bajo un <b>modelo híbrido de trabajo: 3 días "
            "remotos y 2 días presenciales por semana</b>. Esta distribución "
            "aplica a todas las áreas de la Empresa, con excepción de Recepción y "
            "Servicios Generales, cuyas funciones son íntegramente presenciales.",
            "Los <b>martes son de presencia obligatoria</b> en la sede de Surco "
            "para todo el equipo, sin excepciones. Ese día se concentran las "
            "reuniones de planificación, las sesiones de trabajo con clientes y "
            "las actividades de integración. El segundo día presencial lo define "
            "cada área y se comunica al inicio de cada trimestre; una vez fijado, "
            "solo puede modificarse con aprobación del jefe de área.",
            "La solicitud de <b>trabajo remoto completo (100 % remoto) requiere "
            "la aprobación del jefe de área</b> y el visto bueno de Gestión "
            "Humana. Se tramita mediante el formulario FR-GH-014 disponible en la "
            "intranet, con una anticipación mínima de 15 días calendario. Las "
            "autorizaciones se otorgan por periodos renovables de 6 meses y se "
            "evalúan según el cumplimiento de objetivos del colaborador.",
            "La Empresa otorga un <b>subsidio mensual de conectividad de "
            "S/ 120</b> a todo colaborador bajo modalidad híbrida o remota, "
            "abonado junto con la remuneración. El colaborador debe contar con "
            "una conexión a internet de al menos 50 Mbps y un espacio de trabajo "
            "que permita videollamadas sin interrupciones. Los equipos de cómputo "
            "son provistos por la Empresa y no pueden ser usados por terceros.",
        ],
    ),
    (
        "4. Vacaciones y descanso vacacional",
        [
            "Todo colaborador tiene derecho a <b>30 días calendario de vacaciones "
            "al año</b>, luego de haber cumplido <b>12 meses continuos de "
            "servicios</b> con la Empresa y de cumplir el récord vacacional "
            "establecido por la legislación laboral peruana.",
            "El descanso vacacional puede <b>fraccionarse en periodos no menores "
            "a 7 días calendario</b>, previo acuerdo entre el colaborador y su "
            "jefe de área. Se recomienda que al menos uno de los periodos sea de "
            "15 días continuos. No se aceptan fraccionamientos que dejen saldos "
            "inferiores a 7 días.",
            "La solicitud de vacaciones se registra en el módulo de Gestión "
            "Humana de la intranet con una <b>anticipación mínima de 20 días "
            "calendario</b>. El jefe de área cuenta con 5 días hábiles para "
            "aprobarla o proponer fechas alternativas. Por razones operativas, no "
            "se aprueban vacaciones para más del 25 % del personal de una misma "
            "área en simultáneo.",
            "Las vacaciones no gozadas pueden acumularse hasta un máximo de "
            "<b>dos periodos consecutivos</b>, con autorización expresa de "
            "Gestión Humana. La Empresa notifica trimestralmente a los "
            "colaboradores con saldos vacacionales vencidos y programa su goce de "
            "oficio si no se registra solicitud dentro de los 60 días siguientes.",
        ],
    ),
    (
        "5. Licencias y permisos",
        [
            "<b>Licencia por maternidad:</b> 98 días naturales (49 de descanso "
            "prenatal y 49 de postnatal), ampliables conforme a ley en caso de "
            "parto múltiple o nacimiento con discapacidad. Al retorno, la madre "
            "goza de 1 hora diaria de permiso por lactancia hasta que el menor "
            "cumpla un año de edad.",
            "<b>Licencia por paternidad:</b> 10 días calendario continuos por "
            "ley, que la Empresa amplía voluntariamente a <b>15 días "
            "calendario</b> como beneficio adicional. Debe solicitarse con al "
            "menos 15 días de anticipación a la fecha probable de parto.",
            "<b>Licencia por fallecimiento</b> de cónyuge, padres, hijos o "
            "hermanos: 5 días hábiles con goce de haber, ampliables a 8 días "
            "hábiles si el deceso ocurre fuera del departamento de Lima.",
            "<b>Permiso por matrimonio:</b> 5 días hábiles. <b>Permiso por examen "
            "médico o trámite personal:</b> hasta 4 horas mensuales, acumulables "
            "hasta un tope de 12 horas por trimestre, coordinadas con el jefe "
            "inmediato con 48 horas de anticipación.",
            "<b>Día libre por cumpleaños:</b> cada colaborador dispone de un día "
            "libre remunerado, a tomar dentro del mes de su cumpleaños o del mes "
            "siguiente. No es acumulable ni canjeable por dinero.",
        ],
    ),
    (
        "6. Viáticos, gastos de viaje y reembolsos",
        [
            "Los viajes por motivos de trabajo requieren aprobación previa del "
            "jefe de área y del Gerente de Operaciones, mediante el formulario "
            "FR-ADM-007. La Empresa cubre el transporte, el alojamiento y los "
            "viáticos diarios del colaborador.",
            "El <b>tope de reembolso por viáticos es de S/ 180 por día en viajes "
            "nacionales</b> dentro del territorio peruano. Este monto cubre "
            "alimentación, movilidad local y gastos menores. El alojamiento se "
            "reserva y paga directamente por el área de Administración, por lo "
            "que no consume el tope diario.",
            "Para <b>viajes internacionales, el tope de reembolso es de USD 95 "
            "por día</b>, bajo el mismo criterio de cobertura. La conversión a "
            "soles se realiza al tipo de cambio venta publicado por la SBS el día "
            "de cierre de la rendición.",
            "El colaborador cuenta con un <b>plazo de 10 días hábiles</b>, "
            "contados desde su retorno, para presentar la rendición de gastos con "
            "los comprobantes de pago originales (factura, boleta o ticket) "
            "emitidos a nombre de Andes Data S.A.C., RUC 20548921736. Vencido ese "
            "plazo sin rendición, el monto entregado se descuenta de la planilla "
            "del mes siguiente.",
            "Los gastos sin comprobante válido no son reembolsables. Quedan "
            "expresamente excluidos del reembolso: bebidas alcohólicas, multas de "
            "tránsito, servicios de lavandería personal, propinas superiores al "
            "10 % del consumo y consumos de acompañantes no autorizados.",
        ],
    ),
    (
        "7. Seguridad de la información y manejo de datos de clientes",
        [
            "Andes Data S.A.C. procesa información sensible de sus clientes, por "
            "lo que la seguridad de la información es una responsabilidad "
            "individual de cada colaborador. La Empresa se rige por la Ley "
            "N.° 29733, Ley de Protección de Datos Personales, y por los "
            "lineamientos del estándar ISO/IEC 27001.",
            "Toda la información de clientes debe almacenarse exclusivamente en "
            "los repositorios corporativos autorizados. Está <b>prohibido copiar "
            "datos de clientes a dispositivos personales, unidades USB o "
            "servicios de nube personal</b> (Google Drive personal, Dropbox "
            "personal, WeTransfer u otros).",
            "Las contraseñas corporativas deben tener un mínimo de 12 caracteres, "
            "combinar mayúsculas, minúsculas, números y símbolos, y "
            "<b>renovarse cada 90 días</b>. El doble factor de autenticación "
            "(2FA) es obligatorio para el correo corporativo, el repositorio de "
            "código y los entornos de nube.",
            "Todo incidente de seguridad (pérdida de equipo, acceso no "
            "autorizado, correo sospechoso, filtración de datos) debe reportarse "
            "al área de TI, al correo seguridad@andesdata.pe, dentro de las "
            "<b>2 horas</b> de detectado. El área de TI dispone de 24 horas para "
            "clasificar el incidente y activar el plan de respuesta.",
            "Los acuerdos de confidencialidad (NDA) firmados con clientes "
            "mantienen vigencia <b>hasta 3 años después</b> del término de la "
            "relación laboral del colaborador con la Empresa.",
        ],
    ),
    (
        "8. Código de conducta y ambiente laboral",
        [
            "La Empresa promueve un ambiente de trabajo respetuoso, diverso e "
            "inclusivo. Se prohíbe toda forma de discriminación por razón de "
            "género, edad, origen étnico, orientación sexual, religión, "
            "discapacidad, condición económica o afiliación política.",
            "El hostigamiento sexual y el acoso laboral son faltas graves "
            "sancionadas con el despido. La Empresa cuenta con un Comité de "
            "Intervención frente al Hostigamiento Sexual, integrado por 4 "
            "miembros (2 representantes del empleador y 2 de los colaboradores), "
            "que investiga las denuncias en un plazo máximo de <b>20 días "
            "hábiles</b>.",
            "Los colaboradores deben declarar cualquier <b>conflicto de "
            "intereses</b> (participación societaria en proveedores o clientes, "
            "vínculo familiar con contrapartes, actividades profesionales "
            "paralelas) ante el área de Cumplimiento, dentro de los 5 días "
            "hábiles de conocido el hecho.",
            "Está prohibido aceptar regalos u obsequios de clientes o proveedores "
            "cuyo valor supere los <b>S/ 150</b>. Los obsequios de cortesía "
            "protocolar por encima de ese monto deben entregarse al área de "
            "Cumplimiento para su registro y disposición institucional.",
        ],
    ),
    (
        "9. Capacitación y desarrollo profesional",
        [
            "Cada colaborador dispone de un <b>presupuesto anual de formación de "
            "S/ 3,500</b>, ejecutable en cursos, certificaciones, congresos o "
            "material especializado relacionado con su rol. El presupuesto se "
            "renueva cada 1 de enero y no es acumulable de un año a otro.",
            "Adicionalmente, la Empresa reconoce <b>8 horas mensuales de tiempo "
            "protegido</b> para estudio y experimentación técnica dentro de la "
            "jornada laboral. Estas horas se registran en el sistema como "
            "actividad de formación y no requieren compensación posterior.",
            "Las certificaciones cloud (AWS, Azure, Google Cloud) y de "
            "herramientas de datos (Databricks, Snowflake, Power BI) se financian "
            "al <b>100 % por la Empresa</b>, incluyendo un intento de reintento "
            "en caso de no aprobar. A cambio, el colaborador se compromete a "
            "permanecer 12 meses en la Empresa o a reembolsar el monto "
            "proporcional al tiempo no cumplido.",
            "El área de Gestión del Talento organiza el programa interno "
            "«Andes Academy», con al menos <b>2 sesiones técnicas mensuales</b> "
            "dictadas por colaboradores senior, de asistencia libre y computables "
            "como horas de formación.",
        ],
    ),
    (
        "10. Evaluación de desempeño",
        [
            "El proceso de evaluación de desempeño es <b>semestral</b> y se "
            "ejecuta en las ventanas de <b>junio y diciembre</b> de cada año. "
            "Comprende una autoevaluación, la evaluación del jefe directo y una "
            "retroalimentación de pares (evaluación 180 grados).",
            "La escala de calificación va de <b>1 a 5</b>, donde 1 corresponde a "
            "«no cumple expectativas» y 5 a «supera ampliamente las "
            "expectativas». Se requiere una calificación mínima de <b>3.0</b> "
            "para acceder al bono anual por desempeño.",
            "Los colaboradores con calificación inferior a 2.5 ingresan a un "
            "<b>Plan de Mejora de 90 días</b>, con objetivos medibles y "
            "seguimiento quincenal por parte del jefe de área y de Gestión "
            "Humana.",
            "Los ascensos y ajustes salariales se resuelven en el ciclo de "
            "diciembre y se hacen efectivos con la planilla de <b>marzo</b> del "
            "año siguiente. El bono anual por desempeño equivale a entre <b>0.5 y "
            "2 remuneraciones mensuales</b>, según la calificación obtenida y el "
            "resultado financiero de la Empresa.",
        ],
    ),
    (
        "11. Beneficios corporativos",
        [
            "<b>Seguro médico EPS:</b> la Empresa cubre el 70 % del aporte del "
            "titular y ofrece la afiliación de derechohabientes con descuento por "
            "planilla. La cobertura inicia el mes siguiente al ingreso.",
            "<b>Seguro Vida Ley:</b> contratado desde el primer día de labores, "
            "sin periodo de carencia.",
            "<b>Asignación por alimentación:</b> S/ 300 mensuales entregados vía "
            "tarjeta de consumo, de carácter no remunerativo conforme a ley.",
            "<b>Bono por referidos:</b> S/ 1,200 por cada candidato referido que "
            "sea contratado y supere los 3 meses de permanencia en la Empresa.",
            "<b>Convenios institucionales:</b> descuentos en gimnasios de la red "
            "SmartFit, en programas de posgrado de universidades asociadas (hasta "
            "20 %) y en servicios de salud mental, con 6 sesiones anuales de "
            "terapia psicológica financiadas al 100 % por la Empresa.",
            "<b>Reconocimiento por aniversario:</b> por cada 5 años cumplidos en "
            "la Empresa, el colaborador recibe un bono de S/ 2,000 y 3 días "
            "hábiles de descanso adicional.",
        ],
    ),
    (
        "12. Canal de denuncias y régimen disciplinario",
        [
            "La Empresa dispone de un <b>canal de denuncias confidencial</b> "
            "administrado por un proveedor externo independiente, accesible en "
            "etica.andesdata.pe y en la línea telefónica (01) 480-2255, "
            "disponible las 24 horas del día. Las denuncias pueden presentarse de "
            "forma anónima.",
            "El Comité de Ética acusa recibo de la denuncia en un plazo de "
            "<b>3 días hábiles</b> y emite conclusiones en un máximo de "
            "<b>30 días hábiles</b>. La Empresa garantiza la ausencia de "
            "represalias contra el denunciante de buena fe; toda represalia se "
            "considera falta grave.",
            "El régimen disciplinario contempla, de forma gradual y según la "
            "gravedad del hecho: amonestación verbal, amonestación escrita, "
            "suspensión sin goce de haber de hasta 3 días y despido por falta "
            "grave, conforme al Decreto Supremo N.° 003-97-TR.",
            "Este manual entra en vigencia desde su publicación y será revisado "
            "de forma anual por el Comité de Gestión Humana. Las modificaciones "
            "se comunican por correo corporativo con al menos 15 días calendario "
            "de anticipación a su entrada en vigor.",
        ],
    ),
]


def _estilos() -> dict[str, ParagraphStyle]:
    """Construye los estilos de parrafo usados en el PDF."""
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle(
            "TituloDoc",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=27,
            spaceAfter=8,
        ),
        "subtitulo": ParagraphStyle(
            "SubtituloDoc",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            alignment=1,
            textColor="#444444",
            spaceAfter=3,
        ),
        "seccion": ParagraphStyle(
            "Seccion",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13.5,
            leading=17,
            spaceBefore=14,
            spaceAfter=6,
        ),
        "cuerpo": ParagraphStyle(
            "Cuerpo",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            alignment=TA_JUSTIFY,
            spaceAfter=7,
        ),
    }


def generar_pdf(ruta: Path) -> int:
    """Genera el manual de politicas internas. Devuelve el numero de paginas."""
    estilos = _estilos()

    documento = SimpleDocTemplate(
        str(ruta),
        pagesize=A4,
        leftMargin=2.4 * cm,
        rightMargin=2.4 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
        title="Manual de Politicas Internas - Andes Data S.A.C.",
        author="Andes Data S.A.C. - Gestion Humana",
        subject="Politicas internas v4.2",
    )

    historia: list = [
        Paragraph("Manual de Políticas Internas", estilos["titulo"]),
        Paragraph("<b>ANDES DATA S.A.C.</b>", estilos["subtitulo"]),
        Paragraph(
            "Consultoría de Datos y Analítica &nbsp;&#8226;&nbsp; Lima, Perú",
            estilos["subtitulo"],
        ),
        Paragraph(
            "Versión 4.2 &nbsp;&#8226;&nbsp; Vigente desde el 15 de enero de 2025 "
            "&nbsp;&#8226;&nbsp; Documento de uso interno",
            estilos["subtitulo"],
        ),
        Spacer(1, 0.6 * cm),
    ]

    for titulo, parrafos in SECCIONES:
        historia.append(Paragraph(titulo, estilos["seccion"]))
        for parrafo in parrafos:
            historia.append(Paragraph(parrafo, estilos["cuerpo"]))

    historia.append(Spacer(1, 0.6 * cm))
    historia.append(
        Paragraph(
            "<i>Documento de uso interno. Aprobado por el Comité de Gestión "
            "Humana de Andes Data S.A.C. Prohibida su reproducción total o "
            "parcial fuera de la organización.</i>",
            estilos["cuerpo"],
        )
    )

    documento.build(historia)
    return documento.page


# ===========================================================================
# 2. CSV DE VENTAS
# ===========================================================================

FECHA_INICIO = date(2023, 1, 1)
FECHA_FIN = date(2025, 12, 31)

TOTAL_FILAS = 1200
FILAS_REFUERZO_DIC_2024 = 120  # se concentran en diciembre de 2024

REGIONES = ["Lima", "Arequipa", "Cusco", "Trujillo", "Piura"]
# Lima concentra la mayor parte del negocio, como en una consultora real.
PESOS_REGION = [0.46, 0.18, 0.12, 0.14, 0.10]

# producto -> (categoria, precio unitario minimo, precio unitario maximo).
# La categoria es fija por producto: un mismo producto nunca cambia de
# categoria a lo largo del historico.
CATALOGO: dict[str, tuple[str, float, float]] = {
    "Dashboard Corporativo": ("Licencias", 2500.0, 7500.0),
    "Migracion Cloud": ("Consultoria", 9000.0, 28000.0),
    "Modelo Predictivo": ("Consultoria", 7000.0, 20000.0),
    "Auditoria de Datos": ("Consultoria", 3500.0, 11000.0),
    "Capacitacion Analytics": ("Capacitacion", 450.0, 1800.0),
    "Integracion ERP": ("Consultoria", 6000.0, 17000.0),
    "Data Warehouse": ("Licencias", 15000.0, 45000.0),
}
PRODUCTOS = list(CATALOGO)
PESOS_PRODUCTO = [0.20, 0.12, 0.13, 0.15, 0.22, 0.10, 0.08]

CLIENTES = [
    "Minera Cerro Verde Andino S.A.",
    "Banco Continental del Sur S.A.A.",
    "Textiles Pima Norte S.A.C.",
    "Agroindustrias Chavimochic S.A.",
    "Pesquera Costa Azul S.A.C.",
    "Constructora Los Incas S.A.",
    "Retail Plaza Sur S.A.C.",
    "Transportes Andino Express S.A.C.",
    "Clinica San Bernardo S.A.",
    "Universidad Tecnologica del Pacifico",
    "Seguros Vida Andina S.A.",
    "Distribuidora Molina Hermanos S.A.C.",
    "Cementos Huascaran S.A.A.",
    "Cerveceria Del Valle S.A.C.",
    "Farmacias Salud Total S.A.C.",
    "Telecom Peru Conecta S.A.C.",
    "Inversiones Miraflores S.A.C.",
    "Grupo Logistico Callao S.A.",
    "Alimentos Selva Verde S.A.C.",
    "Hoteles Cusco Imperial S.A.C.",
    "Energia Renovable Ica S.A.C.",
    "Automotriz Lima Norte S.A.C.",
    "Editorial Amauta S.A.C.",
    "Corporacion Avicola Piurana S.A.",
    "Servicios Portuarios Paita S.A.C.",
    "Aceros del Rimac S.A.A.",
    "Inmobiliaria Terra Nova S.A.C.",
    "Laboratorios Quimica Andina S.A.",
    "Supermercados Mi Barrio S.A.C.",
    "Financiera Credi Andes S.A.",
    "Turismo Machu Travel S.A.C.",
    "Plasticos Industriales Ate S.A.C.",
    "Consorcio Vial Sierra Sur S.A.",
    "Gas Natural Altiplano S.A.C.",
    "Frutas de Exportacion Olmos S.A.",
    "Muebles Diseno Trujillo S.A.C.",
    "Seguridad Integral Halcon S.A.C.",
    "Aguas Cristalinas del Norte S.A.",
    "Tecnologia Medica Vitalis S.A.C.",
    "Molinos San Agustin S.A.A.",
]

VENDEDORES = [
    "Ana Quispe",
    "Carlos Mendoza",
    "Lucia Ramirez",
    "Jorge Salazar",
    "Patricia Vargas",
    "Diego Fernandez",
    "Rosa Huaman",
    "Miguel Torres",
]


def _fechas_aleatorias() -> list[date]:
    """Devuelve TOTAL_FILAS fechas dentro del rango, reforzando dic-2024."""
    rango_dias = (FECHA_FIN - FECHA_INICIO).days
    n_uniformes = TOTAL_FILAS - FILAS_REFUERZO_DIC_2024

    fechas = [
        FECHA_INICIO + timedelta(days=random.randint(0, rango_dias))
        for _ in range(n_uniformes)
    ]

    # Refuerzo explicito de diciembre de 2024 (cierre de ano, pico de ventas):
    # garantiza un volumen holgado de filas para ese mes.
    fechas += [
        date(2024, 12, random.randint(1, 31))
        for _ in range(FILAS_REFUERZO_DIC_2024)
    ]
    return fechas


def generar_csv(ruta: Path) -> pd.DataFrame:
    """Genera el historico de ventas y lo guarda en CSV. Devuelve el DataFrame."""
    fechas = _fechas_aleatorias()

    productos = [
        str(p) for p in np.random.choice(PRODUCTOS, size=TOTAL_FILAS, p=PESOS_PRODUCTO)
    ]
    regiones = [
        str(r) for r in np.random.choice(REGIONES, size=TOTAL_FILAS, p=PESOS_REGION)
    ]

    datos = pd.DataFrame(
        {
            "fecha": [f.strftime("%Y-%m-%d") for f in fechas],
            "region": regiones,
            "producto": productos,
            "categoria": [CATALOGO[p][0] for p in productos],
            "cliente": [random.choice(CLIENTES) for _ in range(TOTAL_FILAS)],
            "vendedor": [random.choice(VENDEDORES) for _ in range(TOTAL_FILAS)],
            "cantidad": [random.randint(1, 10) for _ in range(TOTAL_FILAS)],
            "precio_unitario": [
                round(random.uniform(CATALOGO[p][1], CATALOGO[p][2]), 2)
                for p in productos
            ],
        }
    )

    # monto_total se calcula con la MISMA operacion que hara el agente al
    # validar, de modo que la consistencia aritmetica sea exacta en el 100 %
    # de las filas.
    datos["monto_total"] = (datos["cantidad"] * datos["precio_unitario"]).round(2)

    datos = datos.sort_values("fecha", kind="mergesort").reset_index(drop=True)
    datos.to_csv(ruta, index=False, encoding="utf-8")
    return datos


# ===========================================================================
# Punto de entrada
# ===========================================================================


def main() -> None:
    random.seed(SEMILLA)
    np.random.seed(SEMILLA)

    CARPETA_DATOS.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("GENERANDO DOCUMENTOS INTERNOS DE ANDES DATA S.A.C.")
    print("=" * 70)

    paginas = generar_pdf(RUTA_PDF)
    print(f"[OK] PDF  -> {RUTA_PDF}")
    print(
        f"     {len(SECCIONES)} secciones | {paginas} paginas | "
        f"{RUTA_PDF.stat().st_size:,} bytes"
    )

    datos = generar_csv(RUTA_CSV)
    print(f"[OK] CSV  -> {RUTA_CSV}")
    print(
        f"     {len(datos):,} filas | {len(datos.columns)} columnas | "
        f"{RUTA_CSV.stat().st_size:,} bytes"
    )
    print(f"     Rango de fechas: {datos['fecha'].min()} a {datos['fecha'].max()}")
    print(
        "     Filas en diciembre 2024: "
        f"{int(datos['fecha'].str.startswith('2024-12').sum())}"
    )
    print(f"     Monto total facturado: S/ {datos['monto_total'].sum():,.2f}")

    print("=" * 70)
    print("LISTO. Los dos archivos estan en la carpeta data/.")
    print("=" * 70)


if __name__ == "__main__":
    main()
