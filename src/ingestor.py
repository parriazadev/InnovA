import feedparser
import json
from datetime import datetime
import time
import requests
from db_client import DatabaseClient

class InnovationIngestor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def fetch_trends(self):
        """
        Obtiene noticias reales desde los RSS feeds almacenados en Supabase.
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌍 Iniciando escaneo de fuentes RSS Cloud...")
        
        db = DatabaseClient()
        rss_feeds = []
        try:
            sources_data = db.fetch_rss_sources()
            # Convertir a formato del loop: (name, url)
            # Filtramos solo activos si la columna existe, sino todos
            rss_feeds = [(s['name'], s['url']) for s in sources_data if s.get('is_active', True)]
            print(f"   📡 Fuentes recuperadas de DB: {len(rss_feeds)}")
        except Exception as e:
            print(f"   ❌ Error leyendo fuentes de DB: {e}")
            # Fallback
            rss_feeds = [
                ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
                ("MIT Tech Review", "https://www.technologyreview.com/feed/")
            ]

        real_trends = []
        
        for source_name, url in rss_feeds:
            try:
                print(f"  📡 Conectando a {source_name}...")
                resp = self.session.get(url, timeout=10)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.content)
                    
                    if feed.entries:
                        print(f"     ✅ {len(feed.entries)} artículos encontrados.")
                        for entry in feed.entries[:5]:
                            summary_text = entry.get('summary', '') or entry.get('description', '')
                            trend_item = {
                                "id": entry.get('link', str(time.time())),
                                "title": entry.get('title', 'Sin Título'),
                                "source": source_name,
                                "published": entry.get('published', str(datetime.now())),
                                "url": entry.get('link', ''),
                                "summary": summary_text[:500] + "...",
                                "tags": [t.term for t in entry.get('tags', [])] if 'tags' in entry else []
                            }
                            real_trends.append(trend_item)
                    else:
                        print(f"     ⚠️ No se encontraron entradas.")
            except Exception as e:
                print(f"     ❌ Error leyendo {source_name}: {str(e)}")

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Total de tendencias recolectadas: {len(real_trends)}")
        return real_trends

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
