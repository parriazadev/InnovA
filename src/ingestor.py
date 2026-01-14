import feedparser
import json
from datetime import datetime
import time
import requests
from db_client import DatabaseClient

import os
import google.generativeai as genai

class InnovationIngestor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Configurar Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            print("⚠️ GEMINI_API_KEY no encontrada.")
            self.model = None

    def evaluate_news_with_llm(self, title, summary, client_name):
        """
        Usa Gemini para decidir si la noticia es sobre una implementación tecnológica del cliente.
        """
        if not self.model:
            return True, summary # Si no hay modelo, pasamos todo por defecto

        prompt = f"""
        ERES: Analista de Inteligencia Tecnológica.
        
        OBJETIVO: Determinar si el siguiente artículo habla sobre una adopción, implementación o proyecto tecnológico específico de la empresa '{client_name}'.
        
        ARTÍCULO:
        Título: {title}
        Resumen: {summary}
        
        CRITERIOS DE RELEVANCIA:
        - SÍ es relevante si menciona: Migraciones cloud, uso de IA, nuevos sistemas core, digitalización, ciberseguridad, automatización.
        - NO es relevante si es: Resultados financieros puros, cambios de directiva, litigios legales, huelgas, o noticias generales del sector sin mencionar a la empresa específicamente en un contexto tech.
        
        SALIDA (JSON Estricto):
        {{
            "is_relevant": true/false,
            "new_summary": "Resumen de 1 linea enfocando SOLO lo técnico. Si no es relevante, dejar vacío."
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text.replace("```json", "").replace("```", ""))
            return data.get("is_relevant", False), data.get("new_summary", summary)
        except Exception as e:
            print(f"      ⚠️ Error LLM: {e}")
            return True, summary # En caso de duda o error, guardamos.

    def fetch_trends(self):
        """
        Obtiene noticias reales desde los RSS feeds almacenados en Supabase.
        Retorna un generador de logs y resultado final.
        """
        yield {"type": "log", "message": f"[{datetime.now().strftime('%H:%M:%S')}] 🌍 Iniciando escaneo de fuentes RSS Cloud..."}
        
        db = DatabaseClient()
        rss_feeds_data = [] 
        try:
            sources_data = db.fetch_rss_sources()
            rss_feeds_data = [s for s in sources_data if s.get('is_active', True)]
            yield {"type": "log", "message": f"   📡 Fuentes recuperadas de DB: {len(rss_feeds_data)}"}
        except Exception as e:
            yield {"type": "log", "message": f"   ❌ Error leyendo fuentes de DB: {e}"}
            yield {"type": "result", "data": []}
            return

        real_trends = []
        
        for source in rss_feeds_data:
            source_name = source['name']
            url = source['url']
            client_data = source.get('clients') 
            assigned_client_name = client_data.get('name') if client_data else None

            try:
                yield {"type": "log", "message": f"  📡 Conectando a {source_name}..."}
                resp = self.session.get(url, timeout=10)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.content)
                    
                    if feed.entries:
                        count = len(feed.entries)
                        yield {"type": "log", "message": f"     ✅ {count} artículos detectados."}
                        
                        for entry in feed.entries[:5]: # Top 5 recent
                            summary_text = entry.get('summary', '') or entry.get('description', '')
                            title_text = entry.get('title', 'Sin Título')
                            
                            final_summary = summary_text
                            is_relevant = True
                            
                            if assigned_client_name:
                                yield {"type": "log", "message": f"     🧠 Analizando con IA para {assigned_client_name}: '{title_text[:30]}...'"}
                                is_relevant, ai_summary = self.evaluate_news_with_llm(title_text, summary_text, assigned_client_name)
                                if is_relevant:
                                    final_summary = ai_summary
                                    yield {"type": "log", "message": "       ✅ Relevante (Tech)."}
                                else:
                                    yield {"type": "log", "message": "       🚫 Descartado (No Tech)."}
                            
                            if is_relevant:
                                trend_item = {
                                    "id": entry.get('link', str(time.time())),
                                    "title": title_text,
                                    "source": source_name,
                                    "published": entry.get('published', str(datetime.now())),
                                    "url": entry.get('link', ''),
                                    "summary": final_summary[:500] + "..." if len(final_summary) > 500 else final_summary,
                                    "tags": [t.term for t in entry.get('tags', [])] if 'tags' in entry else []
                                }
                                real_trends.append(trend_item)
            except Exception as e:
                yield {"type": "log", "message": f"     ❌ Error leyendo {source_name}: {str(e)}"}

        yield {"type": "log", "message": f"🏁 Ingesta finalizada. Total: {len(real_trends)} tendencias."}
        yield {"type": "result", "data": real_trends}

    def save_trends(self, trends):
        db = DatabaseClient()
        db.save_trends(trends)
        print(f"💾 {len(trends)} tendencias guardadas en Supabase.")

if __name__ == "__main__":
    ingestor = InnovationIngestor()
    trends = ingestor.fetch_trends()
    ingestor.save_trends(trends)

if __name__ == "__main__":
    ingestor = InnovationIngestor()
    trends = ingestor.fetch_trends()
    ingestor.save_trends(trends)
