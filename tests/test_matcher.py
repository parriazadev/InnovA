import pytest
from unittest.mock import MagicMock, patch
import sys
import os
import json

# Asegurar que pytest encuentra 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from matcher import OpportunityMatcher

@pytest.fixture
def mock_db():
    with patch('matcher.DatabaseClient') as MockDB:
        yield MockDB.return_value

@pytest.fixture
def mock_genai():
    with patch('matcher.genai') as MockGenAI:
        yield MockGenAI

def test_initialization_no_key(mock_genai):
    """Verifica que el modelo es None si no hay API KEY"""
    with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
        matcher = OpportunityMatcher()
        assert matcher.model is None

def test_initialization_with_key(mock_genai):
    """Verifica que se configura genai si hay API KEY"""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
        matcher = OpportunityMatcher()
        mock_genai.configure.assert_called_with(api_key="fake_key")
        assert matcher.model is not None

def test_analyze_match_with_llm_success(mock_genai):
    """Verifica que si LLM devuelve JSON válido, se retorna dict correcto"""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
        matcher = OpportunityMatcher()
        
        # Mock del modelo y respuesta
        mock_response = MagicMock()
        mock_response.text = '{"match_score": 85, "reasoning": ["Good fit", "Low cost"], "generated_pitch": "Hello..."}'
        matcher.model.generate_content.return_value = mock_response

        client = {"name": "TestCorp", "industry": "Mining", "tech_context_raw": "Uses Python"}
        trend = {"title": "New AI", "source": "TechCrunch", "summary": "AI is cool"}

        result = matcher.analyze_match_with_llm(trend, client)
        
        assert result["match_score"] == 85
        assert len(result["reasoning"]) == 2
        assert result["generated_pitch"] == "Hello..."

def test_analyze_match_with_llm_malformed_json(mock_genai):
    """Verifica robustez ante respuesta no JSON del LLM"""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
        matcher = OpportunityMatcher()
        
        # Mock respuesta inválida
        mock_response = MagicMock()
        mock_response.text = 'Esto no es JSON'
        matcher.model.generate_content.return_value = mock_response

        client = {"name": "TestCorp"}
        trend = {"title": "New AI"}

        # Debería manejar la excepción y retornar estructura default con error
        result = matcher.analyze_match_with_llm(trend, client)
        
        assert result["match_score"] == 0
        assert "Error LLM" in result["reasoning"][0]

def test_run_matching_cycle(mock_db, mock_genai):
    """Test de integración simulado del ciclo completo"""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
        matcher = OpportunityMatcher()
        
        # Setup datos simulados DB
        mock_db.fetch_clients.return_value = [{"name": "Client A", "tech_context_raw": "None"}]
        mock_db.fetch_trends.return_value = [{"title": "Trend 1", "url": "http://trend1.com"}]
        
        # Setup respuesta LLM
        mock_response = MagicMock()
        mock_response.text = '{"match_score": 95, "reasoning": ["Perfect"], "generated_pitch": "Buy now"}'
        matcher.model.generate_content.return_value = mock_response

        # Ejecutar
        opportunities = matcher.run_matching_cycle()
        
        # Verificar
        assert len(opportunities) == 1
        assert opportunities[0]["client"] == "Client A"
        assert opportunities[0]["match_score"] == 95
