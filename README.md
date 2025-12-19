# 📡 InnovA Radar - AI Corporate Intelligence System

InnovA Radar es un sistema de inteligencia corporativa que utiliza Inteligencia Artificial Generativa (Google Gemini) para cruzar automáticamente tendencias tecnológicas globales con el perfil y necesidades de clientes corporativos.

## 🚀 Características Principales

-   **🕵️ Perfilado Automático**: Enriquecimiento de datos de clientes corporativos (Industria, Tech Stack).
-   **🔌 Ingesta de Tendencias Multifuente**: Sistema de RSS con soporte para fuentes globales y específicas por cliente.
-   **🧠 Matchmaker AI**: Motor de decisión que evalúa la relevancia de una noticia para un cliente específico y genera un "Sales Pitch" personalizado.
-   **📊 Dashboard Interactivo**: Interfaz desarrollada en Streamlit para la gestión de datos, visualización de oportunidades y administración de fuentes.
-   **🛡️ CRM Integrado**: Módulo de gestión de clientes con capacidades CRUD completas.

## 🛠️ Stack Tecnológico

-   **Frontend**: Streamlit
-   **Backend Logic**: Python 3.12+
-   **Base de Datos**: Supabase (PostgreSQL)
-   **IA Engine**: Google Gemini Pro (via `google-generativeai`)
-   **Testing**: Pytest & Mock

## 📦 Instalación y Despliegue

### Requisitos Previos
-   Python 3.10 o superior.
-   Cuenta en Supabase y Google AI Studio (para API Keys).

### Configuración Local

1.  **Clonar el repositorio**:
    ```bash
    git clone https://github.com/tu-usuario/innova-radar.git
    cd innova-radar
    ```

2.  **Instalar dependencias**:
    Se recomienda usar un entorno virtual.
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Mac/Linux
    source .venv/bin/activate
    
    pip install -r requirements.txt
    ```

3.  **Configurar Variables de Entorno**:
    Crea un archivo `.env` en la raíz del proyecto con las siguientes claves:
    ```ini
    GEMINI_API_KEY="tu_api_key_de_google"
    SUPABASE_URL="tu_supabase_project_url"
    SUPABASE_KEY="tu_supabase_anon_key"
    ```

4.  **Ejecutar la Aplicación**:
    ```bash
    streamlit run src/dashboard.py
    ```

## 🧪 Pruebas (TDD)

El proyecto cuenta con una suite de tests unitarios que cubren los módulos críticos (IA, Base de Datos, Ingesta).

Para ejecutar las pruebas:
```bash
python -m pytest
```

## ☁️ Despliegue en Streamlit Cloud

1.  Sube este repositorio a GitHub.
2.  Conecta tu cuenta en share.streamlit.io.
3.  Selecciona el repositorio y el archivo principal (`src/dashboard.py`).
4.  **Importante**: En la configuración "Advanced Settings" de Streamlit Cloud, agrega tus secretos (`GEMINI_API_KEY`, etc.) pegando el contenido de tu `.env`.

---
*Developed by InnovA AI Team*
