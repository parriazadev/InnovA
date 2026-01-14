import streamlit as st
import json
import pandas as pd
import sys
import os
import time

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
    
    # --- Top Actions Row & Selector ---
    db = DatabaseClient()
    clients = db.fetch_clients()
    
    # Selector logic (Moved up)
    client_map = {c['name']: c for c in clients}
    all_client_names = sorted(list(client_map.keys()))
    
    c1, _, c2 = st.columns([2, 1, 2])
    with c1:
        st.title("Radar de Oportunidades")
        st.markdown("Gestión en tiempo real.")
    with c2:
        selected_client_filter = st.selectbox("📂 Filtrar Análisis/Vista:", ["Todos"] + all_client_names)
        trend_limit_val = st.slider("Límite de Tendencias", min_value=1, max_value=20, value=5, help="Define cuántas noticias analizar por cliente")

    # Boton de Analisis (Depende del filtro)
    if st.button("🚀 Ejecutar Análisis IA", type="primary", use_container_width=True):
        matcher = OpportunityMatcher()
        matches = []
        
        # UI Feedback
        target_msg = f"para {selected_client_filter}" if selected_client_filter != "Todos" else "Global"
        
        with st.status(f"🧠 Ejecutando Análisis ({target_msg})...", expanded=True) as status:
            st.write("Iniciando motor cognitivo...")
            
            # Pasamos filtro y limite
            for update in matcher.run_matching_cycle(specific_client_name=selected_client_filter, trend_limit=trend_limit_val):
                if update["type"] == "log":
                    st.write(update["message"])
                elif update["type"] == "result":
                    matches = update["data"]
            
            status.update(label="✅ Análisis Completado!", state="complete", expanded=False)
        
        if matches:
            matcher.save_opportunities(matches)
            st.success(f"Se encontraron {len(matches)} nuevas oportunidades.")
            time.sleep(1)
            st.rerun()
        else:
            st.warning("El análisis terminó sin nuevas oportunidades.")

    st.divider()
    
    opportunities = db.fetch_opportunities()
    
    if not opportunities:
        st.info("No hay oportunidades detectadas aún.")
        return

    # Filter View Logic (Uses the same selector)
    if selected_client_filter != "Todos":
        filtered_ops = [op for op in opportunities if op.get('client_name') == selected_client_filter]
    else:
        filtered_ops = opportunities

    if not filtered_ops:
        st.warning(f"No hay oportunidades guardadas para {selected_client_filter}.")
        return

    # FEED VIEW IMPLEMENTATION
    st.markdown("### Business Opportunity Feed")
    
    # Center column for feed look
    _, feed_col, _ = st.columns([1, 6, 1])
    
    with feed_col:
        for op in filtered_ops:
            client_name = op.get('client_name', 'Unknown')
            client_data = client_map.get(client_name, {})
            industry = client_data.get('industry', 'General')
            score = op.get('match_score', 0)
            
            # Feed Card
            with st.container(border=True):
                # Header: Client & Badge
                h1, h2 = st.columns([3, 1])
                with h1:
                    st.markdown(f"### {client_name}")
                    st.caption(f"Industria: {industry}")
                with h2:
                    # Circular score or Badge
                    color_hex = "#28a745" if score >= 90 else "#ffc107" if score >= 75 else "#17a2b8"
                    st.markdown(f"""
                        <div style="text-align:center; background-color:{color_hex}; color:white; padding:10px; border-radius:10px;">
                            <h2 style="margin:0; padding:0; color:white;">{score}%</h2>
                            <small>Match</small>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Title
                st.markdown(f"## {op.get('trend_title')}")
                
                # Full Content (Pitch)
                st.markdown("#### Sales Pitch")
                st.info(op.get('generated_pitch'))
                
                # Reasoning
                st.markdown("#### Por qué es relevante")
                reasoning = op.get('reasoning')
                if isinstance(reasoning, str):
                    try:
                        reasoning = json.loads(reasoning)
                    except:
                        pass
                
                if isinstance(reasoning, list):
                    for r in reasoning:
                        st.markdown(f"- {r}")
                else:
                    st.markdown(str(reasoning))
                
                # Action Buttons (Mockup)
                b1, b2, b3 = st.columns([1, 1, 4])
                with b1: 
                    if st.button("💾 Guardar", key=f"save_{op.get('id')}"):
                        st.toast(f"✅ Oportunidad para {client_name} guardada exitosamente.")
                with b2:
                    if st.button("❌ Descartar", key=f"dism_{op.get('id')}"):
                        db.delete_opportunity(op.get('id'))
                        st.toast("🗑️ Oportunidad descartada.")
                        time.sleep(0.5)
                        st.rerun()

            st.markdown("---") # Spacer between cards

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

        # --- SECCIÓN DE EDICIÓN (Inline para compatibilidad con versiones antiguas de Streamlit) ---
        if 'editing_client' in st.session_state and st.session_state['editing_client']:
            client_to_edit = st.session_state['editing_client']
            
            with st.container(border=True):
                st.subheader(f"✏️ Editando: {client_to_edit['name']}")
                c_form = st.columns([1, 2])
                with c_form[0]:
                    new_ind = st.text_input("Industria", value=client_to_edit.get('industry', ''))
                with c_form[1]:
                    # AI Generation Button
                    c_label, c_btn = st.columns([1, 1])
                    with c_label:
                        st.write("Contexto Tecnológico")
                    with c_btn:
                        if st.button("✨ Generar con IA", key="gen_ai_ctx", help="Autocompletar usando Gemini", use_container_width=True):
                            with st.spinner("Gemini está investigando a la empresa..."):
                                m_gen = OpportunityMatcher()
                                ai_context = m_gen.generate_tech_context(client_to_edit['name'], client_to_edit.get('industry'))
                                # Update session state to reflect in text_area on rerun
                                st.session_state['temp_edit_context'] = ai_context
                                st.rerun()

                    # Value logic: priority to temp_gen -> db_value -> empty
                    curr_val = st.session_state.get('temp_edit_context', client_to_edit.get('tech_context_raw', ''))
                    new_ctx = st.text_area("Contexto", value=curr_val, height=200, label_visibility="collapsed")
                
                b_save, b_cancel = st.columns([1, 4])
                with b_save:
                    if st.button("💾 Guardar Cambios", type="primary"):
                        db.update_client(client_to_edit['id'], new_ind, new_ctx)
                        st.success("Cliente actualizado.")
                        del st.session_state['editing_client']
                        if 'temp_edit_context' in st.session_state: del st.session_state['temp_edit_context'] # Cleanup
                        st.rerun()
                with b_cancel:
                    if st.button("❌ Cancelar"):
                        del st.session_state['editing_client']
                        if 'temp_edit_context' in st.session_state: del st.session_state['temp_edit_context'] # Cleanup
                        st.rerun()
            st.divider()
        # -------------------------------------------------------------------------------------------

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
                c_edit, c_del = st.columns(2)
                with c_edit:
                    if st.button("✏️", key=f"edit_cli_{c.get('id')}", help="Editar Contexto"):
                        st.session_state['editing_client'] = c
                        st.rerun()
                with c_del:
                    if st.button("🗑️", key=f"del_cli_{c.get('id')}", help="Eliminar Cliente"):
                        db.delete_client(c.get('id'))
                        st.rerun()
            
            st.markdown("---")

    with tab2:
        st.subheader("Ingesta de Tendencias")
        st.info("Utilice este módulo para forzar una actualización manual de todas las fuentes RSS.")
        if st.button("🔄 Ejecutar Motor de Ingesta (RSS)"):
            ingestor = InnovationIngestor()
            trends = []
            
            with st.status("📡 Escaneando fuentes distribuidas e Inteligencia...", expanded=True) as status:
                st.write("Conectando con feeds...")
                
                # Consumir generador de logs
                for update in ingestor.fetch_trends():
                    if update["type"] == "log":
                        st.write(update["message"])
                    elif update["type"] == "result":
                        trends = update["data"]
                
                status.update(label=f"✅ Ingesta Completada! ({len(trends)} arts)", state="complete", expanded=False)

            if trends:
                ingestor.save_trends(trends)
                st.success(f"Se procesaron {len(trends)} artículos nuevos.")
                time.sleep(2)
                st.rerun()


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

    # Header
    h1, h2, h3, h4, h5 = st.columns([1, 4, 1.5, 1.5, 1])
    h1.markdown("**Activa**")
    h2.markdown("**Nombre**")
    h3.markdown("**Categoría**")
    h4.markdown("**Asignación**")
    h5.markdown("**Acciones**")
    st.divider()

    for s in sources:
        r1, r2, r3, r4, r5 = st.columns([1, 4, 1.5, 1.5, 1])
        
        with r1:
            # Toggle de estado
            is_active = s.get('is_active', True)
            if st.toggle("", value=is_active, key=f"toggle_{s['id']}"):
                if not is_active: # If it WAS inactive and now is active
                     db.update_source_status(s['id'], True)
                     # Optional: st.rerun() if immediate visual update needed beyond toggle state
            else:
                if is_active: # If it WAS active and now is inactive
                     db.update_source_status(s['id'], False)

        with r2:
            st.markdown(f"**{s['name']}**")
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
