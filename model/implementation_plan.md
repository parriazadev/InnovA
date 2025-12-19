# Plan de Implementación: Radar de Innovación Proactiva

## Objetivo
Crear una herramienta interna que automatice la vigilancia tecnológica y genere oportunidades comerciales proactivas, cruzando **Innovaciones Globales** con el **Contexto Específico del Cliente**.

## Problema a Resolver
Los clientes evolucionan rápido. La consultora reacciona tarde. Necesitamos pasar de un modelo reactivo ("¿Qué necesitas?") a uno proactivo ("Esto es lo que tu stack actual permite hacer hoy con la nueva tecnología X").

## Arquitectura Propuesta

### 1. Módulo de Ingesta (REAL)
- **Tecnología:** Librería `feedparser` + `requests`.
- **Fuentes Reales:**
  - RSS TechCrunch: `https://techcrunch.com/feed/`
  - RSS YCombinator: `https://news.ycombinator.com/rss`
  - RSS AWS News: `https://aws.amazon.com/about-aws/whats-new/recent/feed/`
- **Output:** Base de datos viva `trends.sqlite` (no json estático).

### 2. Módulo de Contexto (REAL)
- **Tecnología:** `googlesearch-python` (Búsqueda) + `BeautifulSoup4` (Extracción).
- **Flujo:**
  1. Input: "Falabella".
  2. Google Search: "Falabella stack tecnologico linkedin jobs".
  3. Scrape: Extraer texto real de las URLs encontradas.
  4. Output: Texto crudo para análisis.

### 3. Motor de Recomendación (REAL)
- **Tecnología:** `LangChain` + `OpenAI API` (requiere KEY) o `Ollama` (Local).
- **Lógica:**
  - Prompt del Sistema: "Eres un consultor experto. Analiza este texto de ofertas de trabajo extraído de {cliente} y extrae el stack tecnológico en JSON."
  - Prompt de Matching: "Tengo esta noticia {noticia} y este perfil {cliente}. ¿Hay oportunidad de negocio? Responde SI/NO y justifica."

### 4. Generador de Entregables (La "Acción")
Generación automática de un "One-Pager" o "Pitch deck slide" para el Manager.
- **Contenido:** Resumen de la tech, Por qué hace fit con el Cliente X, Estimación de esfuerzo, Valor de negocio.

## Estructura de Archivos Propuesta

### Backend (Python/FastAPI)
- `src/ingestor.py`: Scripts para obtener data de RSS/APIs externas.
- `src/client_db.json`: Mock data de clientes chilenos.
- `src/matcher.py`: Lógica principal de cruce.

### Frontend (Streamlit - MVP Rápido)
- `src/dashboard.py`: Interfaz de usuario para visualizar oportunidades, ejecutar el match y enriquecer clientes manualmente.
- Ventaja: Conexión directa con `matcher.py` sin necesidad de API REST intermedia.
