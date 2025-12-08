from fastapi import FastAPI, HTTPException
import re
from pydantic import BaseModel
from typing import List, Optional
from .ia_busqueda import IABusqueda
# Importas tu modelo ya cargado
from .modelo_vectores import vocabulario, idf, u, d0, d2, similitudes_por_documento
from .procesar_texto import normalizar_y_filtrar, aplicar_stemming
from .modelo_vectores import buscar_top_por_consulta, recomendacion_completa


import numpy as np
import re
import time
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "https://upscholar-fonted.onrender.com",  # frontend deployado en Render
    "http://localhost",
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    texto: str
    top_k: int = 10

class QueryIA(BaseModel):
    texto: str
    top_k: int = 10  # Artículos principales
    recomendaciones_por_item: int = 3 

class RecomendacionRequest(BaseModel):
    indice_documento: int
    top_k: int = 3
    excluir_indices: Optional[List[int]] = None
    usar_ia: bool = False  # Nuevo: elegir entre TF-IDF o IA

# ================= INICIALIZACIÓN DE IA =================

# ================= INICIALIZACIÓN DE IA =================

ia_busqueda = None

try:
    # Leer API key de variable de entorno o archivo .env
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # También intentar leer de archivo .env si existe
    if not GOOGLE_API_KEY and os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("GOOGLE_API_KEY="):
                    GOOGLE_API_KEY = line.strip().split("=")[1]
                    break
    
    # Si aún no hay, usar una variable alternativa
    if not GOOGLE_API_KEY:
        # Verificar si hay API key hardcodeada como variable
        GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
    
    if GOOGLE_API_KEY:
        print("Inicializando búsqueda con IA...")
        print(f"API Key encontrada: {GOOGLE_API_KEY[:10]}...")
        
        ia_busqueda = IABusqueda(gemini_api_key=GOOGLE_API_KEY)
        ia_busqueda.inicializar(d2, d0)
        
        if ia_busqueda.embeddings_matrix is not None:
            print("✓ Búsqueda con IA inicializada correctamente")
        else:
            print("⚠ IA inicializada pero sin embeddings (modo fallback)")
            ia_busqueda = None
    else:
        print("⚠ Google API Key no encontrada. Búsqueda IA deshabilitada")
        print("  Crea un archivo .env con: GOOGLE_API_KEY=tu_api_key")
        
except ImportError as e:
    print(f"⚠ Módulo IA no disponible: {e}")
    ia_busqueda = None
except Exception as e:
    print(f"⚠ Error inicializando búsqueda IA: {e}")
    print(f"  Detalles: {str(e)}")
    import traceback
    traceback.print_exc()
    ia_busqueda = None

# ================= FUNCIONES AUXILIARES =================

def generar_snippet_mejorado(texto: str, tokens: List[str], max_longitud: int = 300) -> str:
    """
    Genera un snippet con múltiples zonas del texto donde aparecen los términos de búsqueda.
    """
    if not texto:
        return "Sin abstract disponible."
    
    texto_lower = texto.lower()
    snippets = []
    
    # Para cada token, encontrar todas sus posiciones
    for token in tokens:
        if len(token) > 2:
            pattern = re.compile(re.escape(token), re.IGNORECASE)
            matches = list(pattern.finditer(texto))
            
            for match in matches[:3]:  # Tomar hasta 3 ocurrencias por token
                start = max(0, match.start() - 40)
                end = min(len(texto), match.end() + 40)
                
                snippet = texto[start:end]
                # Resaltar el token encontrado
                snippet = pattern.sub(lambda m: f"<b>{m.group(0)}</b>", snippet)
                
                # Agregar puntos suspensivos si es necesario
                if start > 0:
                    snippet = "..." + snippet
                if end < len(texto):
                    snippet = snippet + "..."
                
                snippets.append(snippet)
    
    # Si no se encontraron coincidencias, tomar el inicio del texto
    if not snippets:
        snippet = texto[:max_longitud]
        if len(texto) > max_longitud:
            snippet = snippet + "..."
        return snippet
    
    # Eliminar duplicados y limitar el número de snippets
    snippets_unicos = []
    for s in snippets:
        if s not in snippets_unicos and len(s) > 10:
            snippets_unicos.append(s)
    
    # Unir los snippets con " ... "
    resultado = " ... ".join(snippets_unicos[:3])  # Máximo 3 zonas
    
    # Limitar la longitud total
    if len(resultado) > max_longitud:
        resultado = resultado[:max_longitud] + "..."
    
    return resultado
def resaltar_palabras(texto: str, palabras: List[str]) -> str:
    """
    Resalta las palabras encontradas en el texto con <mark>
    """
    if not texto or not palabras:
        return texto
    
    texto_resaltado = texto
    for palabra in palabras:
        # Buscar la palabra ignorando mayúsculas/minúsculas y con límites de palabra
        patron = re.compile(r'\b(' + re.escape(palabra) + r')\b', re.IGNORECASE)
        texto_resaltado = patron.sub(r'<mark>\1</mark>', texto_resaltado)
    
    return texto_resaltado

# ================= ENDPOINTS =================

@app.get("/")
def read_root():
    return {
        "mensaje": "UPSCHOLAR Backend OK", 
        "documentos": len(d0),
        "ia_disponible": ia_busqueda is not None,
        "version": "2.0"
    }

@app.get("/status-ia")
def status_ia():
    """
    Verifica el estado del módulo de IA
    """
    status = {
        "ia_disponible": ia_busqueda is not None,
        "documentos_indexados": len(d0) if ia_busqueda else 0,
    }
    
    if ia_busqueda and hasattr(ia_busqueda, 'embeddings_matrix') and ia_busqueda.embeddings_matrix is not None:
        status["embedding_dimensiones"] = ia_busqueda.embeddings_matrix.shape
    else:
        status["embedding_dimensiones"] = None
        
    return status

# En main.py, elimina o comenta el endpoint /recomendaciones y /recomendaciones-ia
# Y modifica /buscar para usar el sistema completo:

@app.post("/buscar")
def buscar(q: Query):
    """
    Búsqueda tradicional AHORA CON SISTEMA COMPLETO:
    1. Top 10 artículos principales
    2. Para cada principal, 3 adicionales únicos
    3. Sin duplicados
    """
    t0 = time.perf_counter()
    
    try:
        # Usar el sistema completo
        resultados_dict, top_indices = recomendacion_completa(
            query=q.texto,
            top_principal=min(q.top_k, 10), 
            adicionales_por_item=3
        )
        
        # Procesar query para snippets
        tokens_clean = normalizar_y_filtrar(q.texto)
        
        # Formatear resultados
        resultados_formateados = []
        total_adicionales = 0
        
        for doc_idx, data in resultados_dict.items():
            principal = data['principal']
            adicionales = data['adicionales']
            total_adicionales += len(adicionales)
            
            # 1. Artículo principal
            item_principal = {
                "indice": int(principal['indice']),
                "titulo": d0[principal['indice']],
                "similitud": float(principal['score_consulta']),
                "snippet": generar_snippet_mejorado(d2[principal['indice']], tokens_clean),
                "tiene_recomendaciones": True,
                "tipo_busqueda": "tfidf",
                "ranking": principal['ranking']
            }
            
            resultados_formateados.append(item_principal)
            
            # 2. Artículos adicionales
            for adicional in adicionales:
                item_adicional = {
                    "indice": int(adicional['indice']),
                    "titulo": d0[adicional['indice']],
                    "similitud": float(adicional['score_similitud']),
                    "snippet": d2[adicional['indice']][:150] + "..." if len(d2[adicional['indice']]) > 150 else d2[adicional['indice']],
                    "tiene_recomendaciones": False,
                    "tipo_busqueda": "tfidf",
                    "principal_relacionado": int(principal['indice'])
                }
                
                resultados_formateados.append(item_adicional)
        
        t1 = time.perf_counter()
        
        return {
            "tiempo": round(t1 - t0, 4),
            "query": q.texto,
            "total_resultados": len(resultados_formateados),
            "tipo_busqueda": "tfidf",
            "resultados": resultados_formateados,
            "estadisticas": {
                "principales": len(top_indices),
                "adicionales": total_adicionales,
                "total_unicos": len(top_indices) + total_adicionales
            }
        }
        
    except Exception as e:
        print(f"❌ Error en búsqueda: {e}")
        # Fallback simple
        return {
            "tiempo": 0,
            "query": q.texto,
            "total_resultados": 0,
            "tipo_busqueda": "error",
            "resultados": [],
            "error": str(e)
        }


# En main.py, modifica SOLO el endpoint /buscar-ia:

@app.post("/buscar-ia")
def buscar_con_ia(q: QueryIA):
    """
    Búsqueda semántica usando embeddings de Gemini
    AHORA CON SISTEMA COMPLETO:
    1. Top 10 artículos principales según consulta
    2. Para cada principal, 3 artículos similares
    3. Sin duplicados entre principales y recomendaciones
    """
    if ia_busqueda is None:
        raise HTTPException(
            status_code=503,
            detail="Búsqueda con IA no disponible. Configura GOOGLE_API_KEY en el archivo .env"
        )
    
    t0 = time.perf_counter()
    
    try:
        # 1. Obtener artículos principales de la búsqueda
        resultados_principales = ia_busqueda.buscar(
            query=q.texto,
            top_k=min(q.top_k * 2, 20)  # Pedir más para filtrar
        )
        
        # Limitar a exactamente top_k y eliminar duplicados
        principales_finales = []
        indices_vistos = set()
        
        for res in resultados_principales:
            if res["indice"] not in indices_vistos and len(principales_finales) < q.top_k:
                indices_vistos.add(res["indice"])
                principales_finales.append(res)
        
        # 2. Para cada artículo principal, obtener recomendaciones similares
        resultados_completos = []
        total_recomendaciones = 0
        
        for principal in principales_finales:
            # Obtener recomendaciones para este artículo
            recomendaciones = ia_busqueda.obtener_recomendaciones(
                indice_doc=principal["indice"],
                top_k=3,  # 3 recomendaciones por artículo
                excluir=list(indices_vistos)  # Excluir los ya vistos
            )
            
            # Añadir artículo principal
            principal_formateado = {
                "indice": principal["indice"],
                "titulo": principal["titulo"],
                "similitud": principal["similitud"],
                "snippet": principal["snippet"],
                "abstract": principal["abstract"],
                "tipo_busqueda": "semantica_ia",
                "tiene_recomendaciones": len(recomendaciones) > 0,
                "es_principal": True,
                "principal_relacionado": None
            }
            
            resultados_completos.append(principal_formateado)
            
            # Añadir recomendaciones
            for rec in recomendaciones:
                # Evitar duplicados
                if rec["indice"] not in indices_vistos:
                    indices_vistos.add(rec["indice"])
                    
                    rec_formateado = {
                        "indice": rec["indice"],
                        "titulo": rec["titulo"],
                        "similitud": rec["similitud"],
                        "snippet": rec["abstract"],  # Usar abstract como snippet
                        "abstract": rec["abstract"],
                        "tipo_busqueda": "semantica_ia",
                        "tiene_recomendaciones": False,
                        "es_principal": False,
                        "principal_relacionado": principal["indice"]
                    }
                    
                    resultados_completos.append(rec_formateado)
                    total_recomendaciones += 1
        
        t1 = time.perf_counter()
        
        return {
            "tiempo": round(t1 - t0, 4),
            "query": q.texto,
            "tipo_busqueda": "semantica",
            "total_resultados": len(resultados_completos),
            "resultados": resultados_completos,
            "estadisticas": {
                "principales": len(principales_finales),
                "recomendaciones": total_recomendaciones,
                "total_unicos": len(resultados_completos)
            }
        }
        
    except Exception as e:
        print(f"❌ Error en búsqueda IA: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback: búsqueda simple sin recomendaciones
        try:
            resultados_simples = ia_busqueda.buscar(q.texto, q.top_k)
            t1 = time.perf_counter()
            
            return {
                "tiempo": round(t1 - t0, 4),
                "query": q.texto,
                "tipo_busqueda": "semantica_simple",
                "total_resultados": len(resultados_simples),
                "resultados": resultados_simples,
                "estadisticas": {
                    "principales": len(resultados_simples),
                    "recomendaciones": 0,
                    "total_unicos": len(resultados_simples)
                }
            }
        except:
            return {
                "tiempo": 0,
                "query": q.texto,
                "tipo_busqueda": "error",
                "total_resultados": 0,
                "error": str(e),
                "resultados": []
            }



@app.get("/documento/{indice}")
def obtener_documento(indice: int):
    """
    Obtiene información completa de un documento por su índice.
    """
    if indice < 0 or indice >= len(d0):
        raise HTTPException(
            status_code=404, 
            detail="Documento no encontrado"
        )
    
    return {
        "indice": indice,
        "titulo": d0[indice],
        "abstract": d2[indice],
        "abstract_completo": d2[indice]
    }

@app.get("/health")
def health_check():
    """
    Endpoint de salud para monitoreo
    """
    return {
        "status": "healthy",
        "documentos": len(d0),
        "ia_activa": ia_busqueda is not None,
        "timestamp": time.time()
    }