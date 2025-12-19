import json
import time
from datetime import datetime
from duckduckgo_search import DDGS
import trafilatura
import random

class ClientEnricher:
    def __init__(self):
        pass

    def search_digital_footprint(self, client_name, max_results=3):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Investigando a '{client_name}' en la web real (DuckDuckGo)...")
        query = f'"{client_name}" transformación digital innovación tecnología casos de éxito lanzamientos'
        
        urls = []
        try:
            results = DDGS().text(query, max_results=max_results)
            if results:
                urls = [r['href'] for r in results]
        except Exception as e:
            print(f"  ❌ Error en búsqueda DDG: {e}")
            return None

        print(f"  ✅ {len(urls)} fuentes encontradas: {urls}")
        
        extracted_content = ""
        
        for url in urls:
            print(f"     ⬇️ Descargando y leyendo: {url}...")
            try:
                downloaded = trafilatura.fetch_url(url)
                if downloaded:
                    text = trafilatura.extract(downloaded)
                    if text:
                        print(f"        📄 Texto extraído ({len(text)} caracteres).")
                        extracted_content += f"\n--- FUENTE: {url} ---\n{text[:2000]}\n" # Limitamos caracteres por fuente
            except Exception as e:
                print(f"        ⚠️ Error extrayendo url: {e}")
        
        return extracted_content if extracted_content else None

    def analyze_info(self, client_name, raw_text):
        """
        Aquí conectaríamos el LLM Real.
        Por ahora, guardamos el texto crudo para que el Matcher (o tú) pueda verlo.
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🧠 Procesando información recolectada...")
        
        profile = {
            "id": f"cli_{int(time.time())}",
            "name": client_name,
            "industry": "Detectar con LLM", 
            "tech_context_raw": raw_text,
            "last_updated": str(datetime.now())
        }
        
        return profile

    def enrich_client(self, client_name):
        raw_text = self.search_digital_footprint(client_name)
        if raw_text:
            profile = self.analyze_info(client_name, raw_text)
            return profile
        else:
            print(f"  [!] No se pudo obtener información suficiente para '{client_name}'.")
            return None

if __name__ == "__main__":
    enricher = ClientEnricher()
    client = "Codelco" # Probar con una real
    profile = enricher.enrich_client(client)
    
    if profile:
        print("\n--- PERFIL GENERADO (Preview) ---")
        print(f"Cliente: {profile['name']}")
        if profile['tech_context_raw']:
            print(f"Contexto Recuperado (Primeros 500 chars):")
            print(profile['tech_context_raw'][:500])
        
    # ... import db_client ...
    from db_client import DatabaseClient

    # ... en if __name__ ...
    if profile:
        print("\n--- PERFIL GENERADO (Preview) ---")
        print(f"Cliente: {profile['name']}")
        if profile['tech_context_raw']:
            print(f"Contexto Recuperado (Primeros 500 chars):")
            print(profile['tech_context_raw'][:500])
        
        # Guardar en BD Cloud
        try:
            db = DatabaseClient()
            # Adaptamos al formato que espera upsert_client (ya viene as)
            db.upsert_client(profile)
            print("✅ Perfil guardado en Supabase.")
        except Exception as e:
            print(f"❌ Error guardando en BD: {e}")
