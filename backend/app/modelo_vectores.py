import polars as pl
import numpy as np
import pandas as pd
import re
import time
import sys
import nltk

from nltk.corpus import stopwords
from nltk.metrics import jaccard_distance
from .procesar_texto import normalizar_y_filtrar, aplicar_stemming

nltk.download("stopwords", quiet=True)

print(">>> Cargando datos y generando modelo vectorial...")

inicio = time.perf_counter()

# ================= CARGA CSV =================
try:
    df = pl.read_csv("data/documentos.csv", encoding="latin1")
except Exception as e:
    print(f"Error crítico al leer documentos.csv: {e}")
    sys.exit()

d0 = df["title"].to_list()
d1 = df["keywords"].to_list()
d2 = df["abstract"].to_list()

# ================= NORMALIZACIÓN =================
titulos = [normalizar_y_filtrar(t) for t in d0]
keywords = [normalizar_y_filtrar(t) for t in d1]
abstract = [normalizar_y_filtrar(t) for t in d2]

# ================= STEMMING =================
abstract_stem = aplicar_stemming(abstract)

# ================= TF =================
def matriz_tf(lista_textos):
    inverted_index = {}

    for n_doc, texto in enumerate(lista_textos):
        for pos, token in enumerate(texto, start=1):
            inverted_index.setdefault(token, {})
            inverted_index[token].setdefault(n_doc, [])
            inverted_index[token][n_doc].append(pos)

    terminos = sorted(inverted_index.keys())
    num_docs = len(lista_textos)

    matriz = []
    for termino in terminos:
        fila = [len(inverted_index[termino].get(doc_id, [])) for doc_id in range(num_docs)]
        matriz.append(fila)

    df_tdm = pd.DataFrame(matriz, index=terminos, columns=[f"doc_{i}" for i in range(num_docs)])
    return df_tdm, np.array(matriz), inverted_index

df_tdm, matriz, inverted_index = matriz_tf(abstract_stem)

# ================= WTF =================
def wtf_funcion(m):
    w = np.zeros_like(m, dtype=float)
    mask = m > 0
    w[mask] = 1 + np.log10(m[mask])
    return w

wtf = wtf_funcion(matriz)

# ================= IDF =================
def df_funcion(m):
    return np.sum(m > 0, axis=1)

df_vec = df_funcion(matriz)
num_docs = matriz.shape[1]

def idf_funcion(df_vec, num_docs):
    return np.log10(num_docs / df_vec)

idf = idf_funcion(df_vec, num_docs)

# ================= TF-IDF =================
tf_idf = wtf * idf[:, np.newaxis]

# ================= NORMALIZACIÓN =================
def normalizar_vectores(m):
    normas = np.linalg.norm(m, axis=0, keepdims=True)
    normas[normas == 0] = 1
    return m / normas

u = normalizar_vectores(tf_idf)

# ================= SIMILITUD COMBINADA (JACCARD + COSENO) =================
print(">>> Calculando similitud combinada (Jaccard + Coseno)...")
sim_inicio = time.perf_counter()

# Preparar datos para Jaccard
print(">>> Aplicando stemming a títulos y keywords...")
titulos_stem = aplicar_stemming(titulos)
keywords_stem = aplicar_stemming(keywords)

# Función optimizada para Jaccard
def calcular_matriz_jaccard(lista_docs):
    n = len(lista_docs)
    matriz = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(n):
            d = jaccard_distance(set(lista_docs[i]), set(lista_docs[j]))
            matriz[i, j] = 1 - d
    return matriz

# Calcular similitudes Jaccard
print(">>> Calculando similitud Jaccard para títulos...")
mat_jaccard_titles = calcular_matriz_jaccard(titulos_stem)

print(">>> Calculando similitud Jaccard para keywords...")
mat_jaccard_keywords = calcular_matriz_jaccard(keywords_stem)

# Calcular similitud coseno para abstracts
print(">>> Calculando similitud coseno para abstracts...")
cos_abstract = np.dot(u.T, u)

# Combinar con pesos optimizados
print(">>> Combinando similitudes...")
w_title = 0.2      # Títulos: 15%
w_keywords = 0.3   # Keywords: 35%
w_abstract = 0.5   # Abstract: 50%

matriz_similitudes = (
    w_title * mat_jaccard_titles + 
    w_keywords * mat_jaccard_keywords + 
    w_abstract * cos_abstract
)

# Crear diccionario de similitudes ordenadas
similitudes_por_documento = {}
num_docs = len(d0)

for i in range(num_docs):
    similitudes = matriz_similitudes[i]
    similitudes_lista = [(j, similitudes[j]) for j in range(num_docs) if j != i]
    similitudes_lista.sort(key=lambda x: x[1], reverse=True)
    similitudes_por_documento[i] = [idx for idx, _ in similitudes_lista]

sim_fin = time.perf_counter()
print(f">>> Similitud combinada calculada en {sim_fin - sim_inicio:.4f} segundos.")
print(f">>> Documentos cargados: {num_docs}")
print(f">>> Pesos: Títulos={w_title}, Keywords={w_keywords}, Abstracts={w_abstract}")
print("-" * 60)

vocabulario = list(df_tdm.index)
matriz_similitudes_global = matriz_similitudes  # <-- ¡ESTA LÍNEA ES CLAVE!

fin = time.perf_counter()
print(f">>> Modelo entrenado en {fin - inicio:.4f} segundos.")
print("-" * 60)

modelo = True


# Al final de tu archivo, debe quedar así:

def buscar_top_por_consulta(query, top_k=10):
    """
    1. Vectoriza la consulta del usuario
    2. Calcula similitud con todos los documentos
    3. Retorna los top_k más relevantes
    """
    # Procesar consulta
    tokens = normalizar_y_filtrar(query)
    stem_q = aplicar_stemming([tokens])[0]
    
    # Vectorizar consulta (igual que tus documentos)
    q_vec = np.zeros(len(vocabulario))
    for token in stem_q:
        if token in vocabulario:
            idx = vocabulario.index(token)
            q_vec[idx] += 1
    
    # Aplicar WTF + IDF
    mask = q_vec > 0
    w_q = np.zeros_like(q_vec)
    w_q[mask] = 1 + np.log10(q_vec[mask])
    q_tfidf = w_q * idf
    
    # Normalizar
    norma_q = np.linalg.norm(q_tfidf)
    u_q = q_tfidf / norma_q if norma_q != 0 else q_tfidf
    
    # Calcular similitudes (producto punto con todos los docs)
    scores = np.dot(u_q, u)
    
    # Obtener top_k
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    return top_indices, scores[top_indices]


def recomendacion_completa(query, top_principal=10, adicionales_por_item=3):
    """
    Sistema completo:
    1. Top 10 artículos para la consulta
    2. Para cada artículo, 3 similares adicionales
    3. Sin duplicados
    """
    # Paso 1: Top 10 principales por consulta
    top_indices, top_scores = buscar_top_por_consulta(query, top_k=top_principal)
    
    # Paso 2: Preparar estructura sin duplicados
    excluidos = set(top_indices)  # Los 10 principales están excluidos
    resultados = {}
    
    # Paso 3: Para cada principal, obtener adicionales únicos
    for i, doc_idx in enumerate(top_indices):
        # Obtener lista de similares precalculada
        similares_ordenados = similitudes_por_documento[doc_idx]
        
        # Filtrar: quitar los que ya están excluidos
        adicionales = []
        for candidato in similares_ordenados:
            if candidato not in excluidos:
                adicionales.append(candidato)
                excluidos.add(candidato)  # Evitar duplicados
                
                if len(adicionales) >= adicionales_por_item:
                    break
        
        # Guardar resultado
        resultados[doc_idx] = {
            'principal': {
                'indice': int(doc_idx),
                'titulo': d0[doc_idx],
                'score_consulta': float(top_scores[i]),
                'ranking': i+1
            },
            'adicionales': [
                {
                    'indice': int(adicional),
                    'titulo': d0[adicional],
                    'score_similitud': float(matriz_similitudes_global[doc_idx, adicional])
                }
                for adicional in adicionales
            ]
        }
    
    return resultados, top_indices

# Asegúrate de exportar la nueva variable
__all__ = [
    'vocabulario', 'idf', 'u', 'd0', 'd2', 'similitudes_por_documento', 
    'matriz_similitudes_global', 'titulos_stem', 'keywords_stem',
    'buscar_top_por_consulta', 'recomendacion_completa'  # <-- ¡CORREGIDO!
]