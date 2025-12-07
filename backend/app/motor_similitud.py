import numpy as np

def similitud_coseno(vec_query, matriz_docs):
    """
    Calcula la similitud coseno entre un vector de query y 
    la matriz de vectores normalizados de documentos.
    """
    if vec_query is None or matriz_docs is None:
        return np.zeros(matriz_docs.shape[1])

    return np.dot(vec_query, matriz_docs)
