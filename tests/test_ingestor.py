import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Asegurar que pytest encuentra 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ingestor import InnovationIngestor

# XML de ejemplo para simular un feed RSS
MOCK_RSS_CONTENT = """
<rss version="2.0">
<channel>
    <title>Tech News</title>
    <item>
        <title>AI takes over</title>
        <link>http://technews.com/ai</link>
        <description>The robots are here.</description>
        <pubDate>Thu, 18 Dec 2025 23:00:00 GMT</pubDate>
    </item>
</channel>
</rss>
"""

@pytest.fixture
def mock_db():
    with patch('ingestor.DatabaseClient') as MockDB:
        yield MockDB.return_value

def test_fetch_trends_success(mock_db):
    """Verifica que el ingestor lea fuentes de la DB y parsee el RSS correctamente"""
    
    # 1. Configurar Mock de DB para retornar 1 fuente
    mock_db.fetch_rss_sources.return_value = [
        {"url": "http://mock-feed.com", "name": "MockFeed", "is_active": True}
    ]

    ingestor = InnovationIngestor()

    # 2. Mockear requests.get para devolver XML falso
    with patch('requests.Session.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = MOCK_RSS_CONTENT
        mock_get.return_value = mock_response

        # 3. Ejecutar
        trends = ingestor.fetch_trends()

        # 4. Verificar
        assert len(trends) == 1
        assert trends[0]["title"] == "AI takes over"
        assert trends[0]["url"] == "http://technews.com/ai"
        assert trends[0]["source"] == "MockFeed" # Nota: Usamos el nombre de la fuente de DB, no del XML si lo tenemos.
        # Wait, en el codigo ingestor usamos source_name de DB como source.


def test_fetch_trends_with_db_failure(mock_db):
    """Verifica que el ingestor use fallback si la DB falla"""
    mock_db.fetch_rss_sources.side_effect = Exception("DB Down")
    
    ingestor = InnovationIngestor()

    # Debería usar fallback (2 URLs hardcodeadas por defecto)
    # Mockeamos requests para que fallen rápido o devuelvan vacío para no colgar el test
    with patch('requests.Session.get') as mock_get:
        mock_get.side_effect = Exception("Network Error") 
        
        trends = ingestor.fetch_trends()
        
        # Debe manejar el error gracefully y retornar lista vacía (o lo que se logró bajar)
        assert isinstance(trends, list)
        assert len(trends) == 0  # 0 porque mockeamos network error tambien

def test_save_trends_calls_db(mock_db):
    """Verifica que save_trends delegue al db_client"""
    ingestor = InnovationIngestor()
    dummy_trends = [{"title": "t1"}]
    
    ingestor.save_trends(dummy_trends)
    
    mock_db.save_trends.assert_called_once_with(dummy_trends)
