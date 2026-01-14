import json
import os
import time
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
from db_client import DatabaseClient

# Cargar variables de entorno (.env)
load_dotenv()

class OpportunityMatcher:
    def __init__(self, trends_path=None, clients_path=None):
        # Paths ya no se usan con Supabase, pero mantenemos firma por compatibilidad si es necesario
        self.trends_path = trends_path
        self.clients_path = clients_path
        
        # Configuración de Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("⚠️ ADVERTENCIA: No se encontró GEMINI_API_KEY en el archivo .env")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            # Usamos gemini-flash-latest por eficiencia y compatibilidad
            self.model = genai.GenerativeModel('gemini-flash-latest')

    def load_data(self, limit=20):
        try:
            print("   📥 Descargando datos desde Supabase...")
            db = DatabaseClient()
            self.trends = db.fetch_trends(limit=limit, active_only=True)
            self.clients = db.fetch_clients()
            print(f"   ✅ Cargados {len(self.clients)} clientes y {len(self.trends)} tendencias (Activas).")
        except Exception as e:
            print(f"❌ Error DB: {e}")
            self.trends = []
            self.clients = []

    def analyze_match_with_llm(self, trend, client):
        """
        Envía los datos reales al LLM para un análisis crítico de negocio.
        """
        if not self.model:
            return {"match_score": 0, "reasoning": ["Falta API Key"], "generated_pitch": ""}

           # Prompt Engineering: Rol de Arquitecto de Soluciones TI & Consultor de Negocio
        prompt = f"""
        ACTÚA COMO: Arquitecto de Soluciones TI Senior y Consultor de Desarrollo de Negocio en una Consultora de Software Líder.
        
        TU TAREA: Identificar si la siguiente **Tendencia Tecnológica** habilita una oportunidad para VENDER un proyecto de desarrollo, integración o modernización al **Cliente**.
        
        --- DATOS DEL CLIENTE ---
        Nombre: {client.get('name')}
        Industria: {client.get('industry', 'Desconocida')}
        
        CONTEXTO TECNOLÓGICO (Infraestructura, stack, dolores, proyectos previos - Texto Crudo):
        "{(client.get('tech_context_raw') or '')[:4000]}" 
        
        --- TENDENCIA / NOTICIA ---
        Título: {trend.get('title')}
        Fuente: {trend.get('source')}
        Resumen: {trend.get('summary')}
        
        --- INSTRUCCIONES DE ANÁLISIS ---
        1. Foco en SOLUCIONES: No busques solo "interés genérico". Busca: ¿Podemos migrar algo? ¿Automatizar un proceso? ¿Implementar un lago de datos? ¿Desplegar un modelo de IA local? ¿Modernizar una app legacy?
        2. Conecta con el Contexto: Si el cliente usa Azure, propón soluciones en Azure. Si tiene problemas de logística, propón optimización de rutas, etc.
        3. Se Proactivo: La propuesta debe sonar a "Podemos construir esto para ustedes".
        
        --- FORMATO DE SALIDA (JSON Estricto) ---
        {{
            "match_score": <numero_0_a_100>,
            "reasoning": [
                "Punto 1: Oportunidad técnica detectada (ej. 'La noticia sobre Copilot sugiere una integración con su CRM actual').",
                "Punto 2: Valor de negocio (ej. 'Reducción de costes operativos en un 15%').",
                "Punto 3: Viabilidad basada en su stack actual."
            ],
            "generated_pitch": "Borrador de correo directo al CTO/Gerente. Tono: Profesional, directo, proponiendo una reunión para presentar una Prueba de Concepto (PoC) o Arquitectura. Menciona tecnologías específicas."
        }}
        """

        try:
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            return json.loads(response.text)
        except Exception as e:
            print(f"⚠️ Error en llamada a Gemini: {e}")
            return {"match_score": 0, "reasoning": [f"Error LLM: {str(e)}"], "generated_pitch": ""}

    def generate_tech_context(self, client_name, industry_hint=None):
        """
        Genera un perfil tecnológico estratégico usando el conocimiento interno del LLM.
        """
        if not self.model:
            return "Error: API Key no configurada."

        prompt = f"""
        ACTÚA COMO: CTO y Estratega de Tecnología.
        OBJETIVO: Generar un 'Perfil Tecnológico' resumido para la empresa: {client_name} (Industria: {industry_hint or 'General'}).
        
        INSTRUCCIONES:
        Basándote en tu conocimiento público entrenado, describe en 3 párrafos breves:
        1. Stack Tecnológico Probable (Cloud, ERPs, Lenguajes).
        2. Principales desafíos de digitalización en su sector hoy.
        3. Áreas donde suelen invertir (ej. Ciberseguridad, Automatización, IA).
        
        FORMATO: Texto plano directo, profesional y listo para ser guardado como contexto interno.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error al generar contexto: {e}"

    def run_matching_cycle(self, specific_client_name=None, trend_limit=5):
        yield {"type": "log", "message": f"[{datetime.now().strftime('%H:%M:%S')}] 🧠 Iniciando análisis cognitivo con Gemini..."}
        self.load_data(limit=trend_limit)
        
        # Filtering Logic
        if specific_client_name and specific_client_name != "Todos":
            self.clients = [c for c in self.clients if c['name'] == specific_client_name]
            if not self.clients:
                 yield {"type": "log", "message": f"⚠️ Cliente '{specific_client_name}' no encontrado en DB."}
        
        opportunities = []
        
        if not self.model:
            yield {"type": "log", "message": "🚫 Deteniendo: Falta configurar API Key."}
            yield {"type": "result", "data": []}
            return

        yield {"type": "log", "message": f"📊 Datos cargados: {len(self.clients)} clientes, {len(self.trends)} tendencias."}

        for client in self.clients:
            yield {"type": "log", "message": f"🏢 Analizando cartera de: {client['name']}..."}
            # Analizamos las top N tendencias para tener variedad sin saturar la API
            for trend in self.trends[:trend_limit]: 
                yield {"type": "log", "message": f"   ⚡ Cruzando con: {trend['title'][:40]}..."}
                
                analysis = self.analyze_match_with_llm(trend, client)
                score = analysis.get('match_score', 0)
                
                # Guardamos incluso score bajo para validar que funcionó, aunque filtremos en UI
                if score > 10: 
                    yield {"type": "log", "message": f"      🚀 MATCH DETECTADO ({score}%): {trend['title'][:30]}..."}
                    result = {
                        "client": client['name'],
                        "trend": trend['title'],
                        "trend_url": trend.get('url'),
                        "match_score": score,
                        "reasoning": analysis.get('reasoning', []),
                        "generated_pitch": analysis.get('generated_pitch', ''),
                        "timestamp": str(datetime.now())
                    }
                    opportunities.append(result)
                    
                    # Delay significativo debido a cuota Free Tier (RPM límite)
                    yield {"type": "log", "message": "      ⏳ Esperando 5s por quota API..."}
                    time.sleep(5) 
        
        yield {"type": "result", "data": opportunities}

    def save_opportunities(self, opportunities):
        db = DatabaseClient()
        print(f"💾 Guardando {len(opportunities)} oportunidades en Cloud...")
        for op in opportunities:
             data = {
                    "client_name": op.get("client"),
                    "trend_title": op.get("trend"),
                    "match_score": op.get("match_score"),
                    "reasoning": op.get("reasoning"), 
                    "generated_pitch": op.get("generated_pitch")
             }
             db.save_opportunity(data)
        print("✅ Guardado exitoso.")

if __name__ == "__main__":
    matcher = OpportunityMatcher()
    matches = matcher.run_matching_cycle()
    if matches:
        matcher.save_opportunities(matches)
