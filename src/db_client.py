import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class DatabaseClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseClient, cls).__new__(cls)
            cls._instance.init_connection()
        return cls._instance

    def init_connection(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("Faltan credenciales de Supabase en .env")
            
        self.client: Client = create_client(url, key)

    def fetch_clients(self):
        response = self.client.table("clients").select("*").execute()
        return response.data

    def upsert_client(self, client_data):
        # Sanitizar: Remover ID si viene del enricher (es mock string)
        # La DB genera su propio ID numérico
        data_to_save = client_data.copy()
        if "id" in data_to_save:
            del data_to_save["id"]

        # Verificar si existe por nombre
        existing = self.client.table("clients").select("*").eq("name", data_to_save["name"]).execute()
        if existing.data:
            # Update
            client_id = existing.data[0]['id']
            # update(data_to_save) NO debe incluir ID
            response = self.client.table("clients").update(data_to_save).eq("id", client_id).execute()
        else:
            # Insert
            response = self.client.table("clients").insert(data_to_save).execute()
        return response.data

    def delete_client(self, client_id):
        return self.client.table("clients").delete().eq("id", client_id).execute()

    def save_trends(self, trends_list):
        # Limpiar tabla o Upsert? 
        # Para MVP simple: Insertar nuevas (ignorando duplicados por URL si se configuró unique)
        # O borrar antiguas. Para historial, mejor upsert on conflict 'url'.
        
        data = []
        for t in trends_list:
            row = {
                "title": t.get("title"),
                "source": t.get("source"),
                "url": t.get("url"),
                "summary": t.get("summary"),
                "published_at": t.get("published") # Asegurar formato fecha si es posible
            }
            data.append(row)
            
        return self.client.table("trends").upsert(data, on_conflict="url").execute()

    def fetch_trends(self):
        # Traer ultimas 20 ordenadas por fecha
        return self.client.table("trends").select("*").order("published_at", desc=True).limit(20).execute().data

    def save_opportunity(self, opportunity):
        return self.client.table("opportunities").insert(opportunity).execute()

    def fetch_opportunities(self):
        return self.client.table("opportunities").select("*").order("created_at", desc=True).execute().data

    # --- RSS SOURCES MANAGEMENT ---
    def fetch_rss_sources(self):
        # Hacemos un join con clients para mostrar el nombre del cliente si existe
        # Nota: Supabase-py join syntax: select("*, clients(name)")
        return self.client.table("rss_sources").select("*, clients(name)").execute().data

    def add_rss_source(self, name, url, category, client_id=None):
        data = {
            "name": name,
            "url": url,
            "category": category,
            "client_id": client_id
        }
        return self.client.table("rss_sources").insert(data).execute()

    def delete_rss_source(self, source_id):
        return self.client.table("rss_sources").delete().eq("id", source_id).execute()
