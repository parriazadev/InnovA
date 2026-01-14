import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db_client import DatabaseClient

def clean_orphaned_opportunities():
    db = DatabaseClient()
    
    print("📥 Fetching Clients...")
    clients_response = db.fetch_clients()
    valid_client_names = set(c['name'] for c in clients_response)
    print(f"✅ Found {len(valid_client_names)} valid clients: {valid_client_names}")

    print("📥 Fetching Opportunities...")
    opportunities = db.fetch_opportunities()
    
    orphaned_ids = []
    orphaned_names = set()
    
    for op in opportunities:
        c_name = op.get('client_name')
        if c_name not in valid_client_names:
            orphaned_ids.append(op['id'])
            orphaned_names.add(c_name)
            
    print(f"🧐 Found {len(orphaned_ids)} orphaned opportunities.")
    if orphaned_names:
        print(f"⚠️ Orphaned Client Names found: {orphaned_names}")
    
    if orphaned_ids:
        print("🗑️ Deleting orphaned opportunities...")
        for o_id in orphaned_ids:
            # Note: We need to implement delete_opportunity in db_client or do direct call here
            # Since db_client might not have delete_opportunity, we'll try to use the client directly if possible
            # But db_client.client is available.
            try:
                db.client.table("opportunities").delete().eq("id", o_id).execute()
                print(f"   Deleted op {o_id}")
            except Exception as e:
                print(f"   Error deleting {o_id}: {e}")
                
        print("🎉 Cleanup Complete.")
    else:
        print("✨ No orphaned data found.")

if __name__ == "__main__":
    clean_orphaned_opportunities()
