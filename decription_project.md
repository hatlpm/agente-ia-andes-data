# Presentando el desafío final
Si llegamos hasta aquí, significa que estamos preparades para el momento más importante de nuestro recorrido en conjunto. Hoy vamos a presentar nuestro challenge (desafío) final, el Alura Agente. Es el desafío práctico que reúne todo lo que aprendimos hasta ahora en un proyecto real.

Imaginemos el siguiente escenario: fuimos contratades por una empresa —puede ser una fintech (tecnología financiera), una consultora o una startup (empresa emergente)— que tiene grandes volúmenes de documentos internos: manuales, informes, políticas y hojas de cálculo. El problema es que las personas pierden horas buscando información dentro de sus archivos. La solución que se requiere es un agente de inteligencia artificial que cualquier persona colaboradora pueda usar para hacer preguntas y recibir respuestas directas en lenguaje natural, sin necesidad de abrir ningún documento. Eso no es ciencia ficción; es lo que los equipos de tecnología ya están construyendo hoy en empresas reales en todo el mundo. Y es exactamente lo que aprenderemos a hacer aquí.

# Explicando las tres etapas del proyecto
El desafío tiene tres partes principales. Expliquemos cada una.

Primero, elegiremos un documento —puede ser un PDF o un CSV— y crearemos código que lea y procese ese archivo. Es decir, nuestra aplicación entenderá el contenido que hay dentro del documento. Ese documento puede tratar sobre políticas internas de la empresa, datos de ventas de productos o documentación sobre las herramientas y tecnologías que la empresa utiliza. También pondremos a disposición un documento de sugerencia, pero podremos utilizar los documentos que queramos y personalizar nuestro agente, porque este proyecto es nuestro.

En segundo lugar, construiremos un agente de IA que pueda responder preguntas sobre ese documento. Alguien podría escribir, por ejemplo: “¿Cuál fue el producto más vendido en diciembre de 2015?” o “¿Qué lenguajes de programación se usan en el back-end (parte del servidor) de la plataforma de ventas de la empresa?”.

El agente encuentra la respuesta en el documento y la devuelve de forma clara. Así de simple.

En tercer lugar, y aquí está el gran diferencial, vamos a hacer el deploy (implementación) de ese agente en la nube de Oracle (OCI). Eso significa que nuestra aplicación saldrá de nuestra computadora y estará accesible públicamente, ejecutándose de verdad en la nube.

Tres etapas: un proyecto completo, del documento al deploy (implementación).

Describiendo tecnologías y entregables
Ahora, hablemos de las tecnologías. No hace falta alarmarnos por la lista. Sugerimos Python (Python) para escribir el código, LangChain (LangChain) para montar el agente, PyPDF (PyPDF) o Pandas (Pandas) para leer los documentos, y un modelo de lenguaje que puede ser Gemma (Gemma), ChatGPT (ChatGPT), Cohere (Cohere) u otro, para hacer que la magia suceda. Para el deploy (implementación), la sugerencia es OCI Compute (OCI Compute), pero estas son sugerencias, no obligaciones. Si contamos con una herramienta que conocemos mejor y que tenga más sentido para nuestro proyecto, podemos usarla. El proyecto, como dijimos, es de quien lo crea. Lo importante es que la solución que presentemos funcione.

Hablemos entonces de lo que necesitamos entregar. Debemos publicar el código en GitHub (GitHub), con:

Un repositorio organizado.
Un historial de commits (confirmaciones).
Un README bien elaborado, con:
Una descripción de la arquitectura que montamos.
Ejemplos de preguntas y respuestas que el agente puede resolver.
Instrucciones para quien quiera ejecutar el proyecto.
Un enlace o una captura de pantalla de la aplicación corriendo en OCI, para comprobar que el deploy (implementación) realmente funcionó.
Detallando validación y consejos finales
Para la validación, vamos a revisar si la solución funciona, si el código está organizado y si el README explica bien lo que se hizo y muestra el deploy (implementación) en línea. Sin misterio: si entregamos algo funcionando y bien documentado, estará perfecto.

Antes de concluir, tres consejos rápidos que nos van a salvar:

Comencemos siempre por el agente local. Hagamos que funcione primero en nuestra máquina. Solo después pensemos en el deploy (implementación). Muchas personas intentan subir a la nube algo que todavía no funciona localmente, y ahí todo se complica.
Usemos Google Colab (Google Colab) para prototipar. Es gratuito, ya viene con Python (Python) configurado y nos ahorra tiempo de instalación.
No nos quedemos atrapados intentando hacer una interfaz visualmente atractiva. El valor del proyecto está en que el agente funcione, no en la apariencia. Enfoquémonos en lo importante.
Eso es todo; mucho éxito. El soporte está disponible si nos trabamos en algún punto. Ahora vamos a construirlo: ¡podemos lograrlo! ¡Hasta luego!