import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Asegurar que pytest encuentra 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from db_client import DatabaseClient

@pytest.fixture
def mock_supabase():
    with patch('db_client.create_client') as MockCreate:
        mock_client = MagicMock()
        MockCreate.return_value = mock_client
        yield mock_client

def test_singleton(mock_supabase):
    """Verifica que DatabaseClient actúe como Singleton"""
    db1 = DatabaseClient()
    db2 = DatabaseClient()
    assert db1 is db2

def test_fetch_clients(mock_supabase):
    """Verifica la construcción de la query fetch_clients"""
    db = DatabaseClient()
    
    # Mock chain: table().select().execute().data
    mock_execute = MagicMock()
    mock_execute.data = [{"name": "Codelco"}]
    
    db.client.table.return_value.select.return_value.execute.return_value = mock_execute

    clients = db.fetch_clients()
    
    db.client.table.assert_called_with("clients")
    db.client.table.return_value.select.assert_called_with("*")
    assert clients[0]["name"] == "Codelco"

def test_upsert_client_sanitization(mock_supabase):
    """Verifica que upsert_client elimine el campo 'id' antes de guardar"""
    db = DatabaseClient()
    
    # Mock para búsqueda de existente (retorna vacío para forzar insert)
    mock_existing = MagicMock()
    mock_existing.data = []
    
    # Mock para el insert final
    mock_insert = MagicMock()
    mock_insert.data = [{"id": 1, "name": "NewCorp"}]

    # Configurar side_effect para manejar las dos llamadas a execute()
    # 1. select().eq().execute() -> existing
    # 2. insert().execute() -> response
    
    # Es complejo mockear cadenas largas.
    # Enfoque: Mockear los returns de cada paso.
    db.client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_existing
    db.client.table.return_value.insert.return_value.execute.return_value = mock_insert

    client_data = {"name": "NewCorp", "id": "fake_id_123", "industry": "Tech"}
    
    result = db.upsert_client(client_data)

    # Verificar Insert
    args, _ = db.client.table.return_value.insert.call_args
    inserted_data = args[0]
    
    assert "id" not in inserted_data
    assert inserted_data["name"] == "NewCorp"

def test_add_rss_source(mock_supabase):
    """Verifica add_rss_source"""
    db = DatabaseClient()
    db.add_rss_source("Fuente X", "http://x.com", "Tech")
    
    db.client.table.assert_called_with("rss_sources")
    # Verificar que insert fue llamado con los datos correctos
    args, _ = db.client.table.return_value.insert.call_args
    assert args[0]["url"] == "http://x.com"
