import json
from db_client import DatabaseClient
import time

def migrate():
    print("🚀 Iniciando migración de datos a Supabase...")
    db = DatabaseClient()
    
    # 1. Clientes
    try:
        with open("c:/repos/InnovA/src/client_db.json", 'r', encoding='utf-8') as f:
            clients = json.load(f)
            print(f"📦 Migrando {len(clients)} clientes...")
            for c in clients:
                # Adaptar campos al schema
                data = {
                    "name": c.get("name"),
                    "industry": c.get("industry"),
                    "tech_context_raw": c.get("tech_context_raw")
                }
                res = db.upsert_client(data)
                print(f"   ✅ Cliente {c.get('name')} guardado.")
    except Exception as e:
        print(f"   ❌ Error migrando clientes: {e}")

    # 2. Tendencias
    try:
        with open("c:/repos/InnovA/src/trends_db.json", 'r', encoding='utf-8') as f:
            trends = json.load(f)
            print(f"📦 Migrando {len(trends)} tendencias...")
            # db.save_trends maneja lista
            db.save_trends(trends)
            print("   ✅ Tendencias guardadas.")
    except Exception as e:
        print(f"   ❌ Error migrando tendencias: {e}")
        
    # 3. Oportunidades
    try:
        with open("c:/repos/InnovA/src/opportunities_report.json", 'r', encoding='utf-8') as f:
            opportunities = json.load(f)
            print(f"📦 Migrando {len(opportunities)} oportunidades...")
            for op in opportunities:
                data = {
                    "client_name": op.get("client"),
                    "trend_title": op.get("trend"),
                    "match_score": op.get("match_score"),
                    "reasoning": json.dumps(op.get("reasoning")), # Serializar JSON a string si el DB espera JSONB, supabase-py suele manejar auto-conversin pero por si acaso.
                    "generated_pitch": op.get("generated_pitch")
                }
                # Ajuste: el campo en DB es 'jsonb', el cliente de supabase lo maneja directo si pasamos dict/list?
                # Intentemos pasar lista directa en 'reasoning'
                data["reasoning"] = op.get("reasoning")
                
                db.save_opportunity(data)
            print("   ✅ Oportunidades guardadas.")
    except Exception as e:
        print(f"   ❌ Error migrando oportunidades: {e}")

    print("🏁 Migración completada.")

if __name__ == "__main__":
    migrate()
