# utils.py
import numpy as np
import re
from typing import List  # Añade esta importación

def resaltar_texto_html(texto: str, tokens: List[str]) -> str:
    """
    Resalta todas las apariciones de los tokens en el texto con HTML.
    """
    if not texto:
        return ""
    
    texto_resaltado = texto
    for token in tokens:
        if len(token) > 2:
            pattern = re.compile(re.escape(token), re.IGNORECASE)
            texto_resaltado = pattern.sub(
                lambda m: f'<span style="font-weight: bold; color: #0066cc;">{m.group(0)}</span>', 
                texto_resaltado
            )
    
    return texto_resaltado

def formatear_titulo_azul(titulo: str) -> str:
    """
    Formatea el título en color azul para HTML.
    """
    return f'<span style="color: #0066cc; font-weight: bold;">{titulo}</span>'