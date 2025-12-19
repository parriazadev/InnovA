import sys
import os

# Asegurar que pytest encuentra 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

def test_environment_setup():
    """
    Test de Humo: Verifica que pytest corre y puede importar módulos del proyecto.
    """
    try:
        import db_client
        import ingestor
        import matcher
        assert True
    except ImportError as e:
        assert False, f"Fallo al importar módulos src: {e}"

def test_basic_math():
    """Validación simple de pytest"""
    assert 1 + 1 == 2
