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

    def load_data(self):
        try:
            print("   📥 Descargando datos desde Supabase...")
            db = DatabaseClient()
            self.trends = db.fetch_trends()
            self.clients = db.fetch_clients()
            print(f"   ✅ Cargados {len(self.clients)} clientes y {len(self.trends)} tendencias.")
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

        # Prompt Engineering: Rol de Consultor Senior
        prompt = f"""
        ACTÚA COMO: Consultor Senior de Estrategia Tecnológica e Innovación.
        
        TU TAREA: Analizar si la siguiente **Tendencia Tecnológica** representa una oportunidad de negocio real para el **Cliente**.
        
        --- DATOS DEL CLIENTE ---
        Nombre: {client.get('name')}
        Industria (Inferida): {client.get('industry', 'Desconocida')}
        
        CONTEXTO PÚBLICO (Extraído de su web/noticias/empleos - Texto Crudo):
        "{(client.get('tech_context_raw') or '')[:4000]}" 
        (Nota: Usa este contexto para entender qué tecnologías usan, sus dolores y estrategias).
        
        --- TENDENCIA / NOTICIA ---
        Título: {trend.get('title')}
        Fuente: {trend.get('source')}
        Resumen: {trend.get('summary')}
        
        --- INSTRUCCIONES DE SALIDA ---
        Analiza críticamente. No inventes. Si la tecnología NO tiene nada que ver, pon score bajo.
        Responde SOLO en formato JSON estricto con esta estructura:
        {{
            "match_score": <numero_0_a_100>,
            "reasoning": ["razon1", "razon2"],
            "generated_pitch": "Texto breve del correo para el manager sugiriendo la reunión con el cliente."
        }}
        """

        try:
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            return json.loads(response.text)
        except Exception as e:
            print(f"⚠️ Error en llamada a Gemini: {e}")
            return {"match_score": 0, "reasoning": [f"Error LLM: {str(e)}"], "generated_pitch": ""}

    def run_matching_cycle(self):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🧠 Iniciando análisis cognitivo con Gemini...")
        self.load_data()
        
        opportunities = []
        
        if not self.model:
            print("🚫 Deteniendo: Falta configurar API Key.")
            return []

        for client in self.clients:
            print(f"  🏢 Analizando cartera de: {client['name']}...")
            # Limitamos a analiz solo 1 tendencia por cliente para evitar error 429
            for trend in self.trends[:1]: 
                print(f"     ⚡ Cruzando con: {trend['title'][:40]}...")
                
                analysis = self.analyze_match_with_llm(trend, client)
                score = analysis.get('match_score', 0)
                print(f"        👉 Score: {score}")
                
                # Guardamos incluso score bajo para validar que funcionó, aunque filtremos en UI
                if score > 10: 
                    print(f"        🚀 MATCH DETECTADO: {trend['title']}")
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
                    print("        ⏳ Esperando 5s por quota...")
                    time.sleep(5) 
        
        return opportunities

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
