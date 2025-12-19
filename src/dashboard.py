import streamlit as st
import json
import pandas as pd
import sys
import os

# Asegurar que podemos importar los módulos locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_client import DatabaseClient
from matcher import OpportunityMatcher
from profile_enricher import ClientEnricher
from ingestor import InnovationIngestor

# Configuración de página - Debe ser lo primero
st.set_page_config(page_title="InnovA Radar", page_icon="📡", layout="wide")

# --- FUNCIONES DE PAGINAS ---

def render_sidebar():
    st.sidebar.title("📡 InnovA Radar")
    st.sidebar.caption("Enterprise Innovation System")
    
    # Navegación Principal
    page = st.sidebar.radio("Navegación", ["Radar de Oportunidades", "Gestión de Datos", "Fuentes de Información"])
    
    st.sidebar.divider()
    
    # Widget de Estado (Mini)
    st.sidebar.caption("Estado del Sistema")
    st.sidebar.markdown("✅ **Database**: *Connected*")
    st.sidebar.markdown("✅ **AI Engine**: *Ready*")
    
    return page

def page_opportunities():
    st.title("Radar de Oportunidades")
    st.markdown("Monitor de inteligencia en tiempo real cruzando tendencias globales con nuestra cartera.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("💡 Este panel muestra las oportunidades de negocio detectadas por el motor de IA.")
    with col2:
        if st.button("🚀 Ejecutar Análisis IA", type="primary", use_container_width=True):
            with st.spinner("Analizando tendencias vs clientes..."):
                matcher = OpportunityMatcher()
                matches = matcher.run_matching_cycle()
                matcher.save_opportunities(matches)
            st.success("Análisis completado.")
            st.rerun()

    st.divider()
    
    db = DatabaseClient()
    opportunities = db.fetch_opportunities()

    if not opportunities:
        st.warning("No hay oportunidades recientes.")
        return

    for op in opportunities:
        score = op.get('match_score')
        client = op.get('client_name')
        trend = op.get('trend_title')
        reasoning = op.get('reasoning')
        
        # Procesar reasoning
        if isinstance(reasoning, str):
            try:
                reasoning = json.loads(reasoning)
            except:
                reasoning = [reasoning]
        
        # Determinar color según score
        color = "red" if score > 90 else "orange" if score > 75 else "blue"
        
        with st.expander(f"🌟 [{score}%] {client} + {trend}"):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"**Pitch Sugerido**")
                st.code(op.get('generated_pitch'), language="text")
                st.markdown("**Por qué es relevante**")
                if isinstance(reasoning, list):
                    for r in reasoning:
                        st.markdown(f"- {r}")
                else:
                    st.markdown(f"- {reasoning}")
            with c2:
                st.metric("Score", f"{score}/100")
                if score > 90:
                    st.error("MATCH CRÍTICO")

def page_data_management():
    st.title("Gestión de Datos Maestros")
    
    tab1, tab2 = st.tabs(["👥 Directorio de Clientes (CRM)", "📥 Ingesta Manual"])
    
    with tab1:
        # --- HEADER & SEARCH ---
        c1, c2 = st.columns([3, 1])
        with c1:
            search_query = st.text_input("🔍 Buscar cliente por nombre...", placeholder="Escribe para filtrar...")
        with c2:
            # Botón primario grande para agregar
            with st.popover("➕ Nuevo Cliente", use_container_width=True):
                st.markdown("### Agregar Cliente")
                new_client = st.text_input("Nombre de la empresa")
                if st.button("🕵️ Investigar y Guardar", type="primary"):
                    with st.spinner("Perfiliando..."):
                        enricher = ClientEnricher()
                        profile = enricher.enrich_client(new_client)
                        if profile:
                            db = DatabaseClient()
                            db.upsert_client(profile)
                            st.success("Guardado éxito.")
                            st.rerun()
                        else:
                            st.error("No se encontró huella digital.")

        st.divider()

        # --- CLIENT TABLE ---
        db = DatabaseClient()
        clients = db.fetch_clients()
        
        # Filtrado search
        if search_query:
            clients = [c for c in clients if search_query.lower() in c['name'].lower()]

        if not clients:
            st.info("No se encontraron clientes.")
            return

        # Table Header
        h1, h2, h3, h4 = st.columns([2, 1.5, 3, 1])
        h1.markdown("**Cliente**")
        h2.markdown("**Industria**")
        h3.markdown("**Contexto Tecnológico (Extracto)**")
        h4.markdown("**Acciones**")
        st.divider()

        for c in clients:
            r1, r2, r3, r4 = st.columns([2, 1.5, 3, 1])
            with r1:
                st.markdown(f"### {c['name']}")
                st.caption(f"ID: {c.get('id', '-')}")
            with r2:
                # Industria Badge logic
                ind = c.get('industry', 'Desconocido')
                if "Minería" in ind:
                    st.markdown(f":orange-background[{ind}]")
                elif "Banca" in ind or "Financ" in ind:
                    st.markdown(f":green-background[{ind}]")
                elif "Retail" in ind:
                    st.markdown(f":blue-background[{ind}]")
                else:
                    st.markdown(f":grey-background[{ind}]")
            with r3:
                raw = c.get('tech_context_raw') or "Sin datos."
                st.caption(raw[:150] + "...")
            with r4:
                # Acciones 
                if st.button("🗑️", key=f"del_cli_{c.get('id')}", help="Eliminar Cliente"):
                    db.delete_client(c.get('id'))
                    st.rerun()
            
            st.markdown("---")

    with tab2:
        st.subheader("Ingesta de Tendencias")
        st.info("Utilice este módulo para forzar una actualización manual de todas las fuentes RSS.")
        if st.button("🔄 Ejecutar Motor de Ingesta (RSS)"):
            with st.spinner("Escaneando fuentes distribuidas..."):
                ingestor = InnovationIngestor()
                trends = ingestor.fetch_trends()
                ingestor.save_trends(trends)
            st.success(f"Se procesaron {len(trends)} artículos nuevos.")


def page_sources():
    st.title("Fuentes de Información")
    st.markdown("Gestión de feeds RSS y orígenes de datos para el motor de inteligencia.")
    
    # Botón Añadir (Modal simulado con expander o form top)
    with st.expander("➕ Agregar Nueva Fuente RSS", expanded=False):
        c1, c2, c3, c4 = st.columns([2, 3, 2, 2])
        with c1:
            s_name = st.text_input("Nombre Fuente")
        with c2:
            s_url = st.text_input("URL RSS")
        with c3:
            s_cat = st.selectbox("Categoría", ["Tecnología", "Minería", "Finanzas", "Retail"])
        with c4:
            # Dropdown Clientes
            db = DatabaseClient()
            clients = db.fetch_clients()
            opts = {c['name']: c['id'] for c in clients}
            s_client = st.selectbox("Asignar a", ["Global"] + list(opts.keys()))
        
        if st.button("Guardar Fuente", type="primary"):
            if s_name and s_url:
                cid = opts.get(s_client) # None si Global
                db.add_rss_source(s_name, s_url, s_cat, cid)
                st.success("Fuente guardada.")
                st.rerun()
            else:
                st.error("Faltan datos.")

    st.divider()

    # TABLA PRINCIPAL
    db = DatabaseClient()
    sources = db.fetch_rss_sources()
    
    if not sources:
        st.info("No hay fuentes configuradas.")
        return

    # Usamos st.dataframe para vista rapida, pero para badges y botones mejor custom layout rows
    
    # Header
    h1, h2, h3, h4, h5 = st.columns([2, 4, 1.5, 1.5, 1])
    h1.markdown("**Nombre**")
    h2.markdown("**URL**")
    h3.markdown("**Categoría**")
    h4.markdown("**Asignación**")
    h5.markdown("**Acciones**")
    st.divider()

    for s in sources:
        r1, r2, r3, r4, r5 = st.columns([2, 4, 1.5, 1.5, 1])
        
        with r1:
            st.markdown(f"**{s['name']}**")
        with r2:
            st.caption(s['url'])
        with r3:
            st.markdown(f"`{s['category']}`")
        with r4:
            # Badge logic
            if s.get('clients'):
                # Cliente especifico -> Azul
                st.markdown(f":blue-background[{s['clients']['name']}]")
            else:
                # Global -> Gris
                st.markdown(f":grey-background[🌐 Global]")
        with r5:
            if st.button("🗑️", key=f"del_{s['id']}", help="Eliminar fuente"):
                db.delete_rss_source(s['id'])
                st.rerun()
        
        st.markdown("---")


# --- MAIN APP FLOW ---
page = render_sidebar()

if page == "Radar de Oportunidades":
    page_opportunities()
elif page == "Gestión de Datos":
    page_data_management()
elif page == "Fuentes de Información":
    page_sources()
