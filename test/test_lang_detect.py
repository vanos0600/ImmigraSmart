import sys
import os
import pytest

# 1. TRUCO DE RUTAS: Le decimos a pytest que busque los archivos en la carpeta 'src'
# Esto DEBE ir antes del import de lang_detect
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir) # Sube a la carpeta principal
src_dir = os.path.join(parent_dir, "src") # Entra a la carpeta src
sys.path.append(src_dir)

# 2. AHORA SÍ importamos tu código real (Python ya sabe dónde buscar)
from lang_detect import detect_language, get_language_instruction

# 3. LAS PRUEBAS
def test_detect_spanish():
    text = "Hola, necesito saber cómo renovar mi visa por favor."
    assert detect_language(text) == "es"

def test_detect_czech():
    text = "Dobrý den, potřebuji pomoct, jsem student."
    assert detect_language(text) == "cs"

def test_detect_english_fallback():
    text = "xyz hello 123"
    assert detect_language(text) == "en"

def test_language_instruction_generation():
    instruction = get_language_instruction("es")
    assert "You MUST respond entirely in Spanish" in instruction
    assert get_language_instruction("en") == ""