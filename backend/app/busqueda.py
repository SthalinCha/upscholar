import numpy as np
from .procesar_texto import normalizar_y_filtrar, aplicar_stemming
from .motor_similitud import similitud_coseno

def buscar_top_k(texto, k, vocab, idf, u, d0, d2):

    tokens = normalizar_y_filtrar(texto)
    stemmed = aplicar_stemming([tokens])[0]

    if not stemmed:
        return {"error": "La búsqueda no contiene términos válidos"}

    q_vec = np.zeros(len(vocab))

    for token in stemmed:
        if token in vocab:
            q_vec[vocab.index(token)] += 1

    if np.sum(q_vec) == 0:
        return {"error": "No hay coincidencias con el vocabulario"}

    mask = q_vec > 0
    w_q = np.zeros_like(q_vec)
    w_q[mask] = 1 + np.log10(q_vec[mask])

    q_tf_idf = w_q * idf
    norma = np.linalg.norm(q_tf_idf)
    q_norm = q_tf_idf / norma if norma != 0 else q_tf_idf

    scores = similitud_coseno(q_norm, u)
    top_ids = np.argsort(scores)[-k:][::-1]

    resultados = []
    for idx in top_ids:
        resultados.append({
            "titulo": d0[idx],
            "abstract": d2[idx],
            "similitud": float(scores[idx])
        })

    return resultados
