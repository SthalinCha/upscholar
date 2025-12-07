"""
Búsqueda semántica usando embeddings de Gemini
"""
import numpy as np
from typing import List, Dict, Any
import re

from .gemini_client import GeminiClient
from .embeddings_manager import EmbeddingsManager
from .procesar_texto import normalizar_y_filtrar

class IABusqueda:
    def __init__(self, gemini_api_key: str = None):
        self.gemini_client = GeminiClient(api_key=gemini_api_key)
        self.embeddings_manager = EmbeddingsManager()
        
        # Cargar o generar embeddings
        self.embeddings_matrix = None
        self.embeddings_norm = None
        self.sim_docs_matrix = None
        self.documentos = []
        self.titulos = []
        

    def inicializar(self, documentos: List[str], titulos: List[str]):
        """
        Inicializa con documentos y genera/calcula embeddings
        """
        try:
            if not documentos or not titulos:
                print("Error: Documentos o títulos vacíos")
                return
            
            self.documentos = documentos
            self.titulos = titulos
            
            print(f"Intentando inicializar IA con {len(documentos)} documentos...")
            
            # MEDIR TIEMPO DE CARGA
            import time
            start_time = time.time()
            
            # Intentar cargar embeddings desde cache
            self.embeddings_matrix = self.embeddings_manager.cargar_embeddings("gemini_embeddings")
            
            # Calcular tiempo transcurrido
            elapsed_time = time.time() - start_time
            print(f"✓ Tiempo de carga de embeddings: {elapsed_time:.2f} segundos")
            
            if self.embeddings_matrix is None:
                print("Generando nuevos embeddings con Gemini...")
                
                # Medir tiempo de generación también si es necesario
                gen_start_time = time.time()
                self.embeddings_matrix = self.gemini_client.generar_embeddings_lote(documentos)
                gen_elapsed_time = time.time() - gen_start_time
                
                print(f"✓ Tiempo de generación de embeddings: {gen_elapsed_time:.2f} segundos")
                
                if self.embeddings_matrix is not None:
                    print(f"Embeddings generados: {self.embeddings_matrix.shape}")
                    self.embeddings_manager.guardar_embeddings(
                        self.embeddings_matrix, 
                        "gemini_embeddings"
                    )
                else:
                    print("No se pudieron generar embeddings")
                    return
            
            # Normalizar y calcular similitudes
            if self.embeddings_matrix is not None:
                self.embeddings_norm = self.embeddings_manager.normalizar_embeddings(
                    self.embeddings_matrix
                )
                self.sim_docs_matrix = self.embeddings_manager.calcular_matriz_similitud(
                    self.embeddings_norm
                )
                print(f"✓ IA Busqueda inicializada con {len(documentos)} documentos")
                print(f"  Embeddings shape: {self.embeddings_matrix.shape}")
            else:
                print("✗ No se pudieron generar embeddings")
                
        except Exception as e:
            print(f"Error crítico inicializando IA: {e}")
            import traceback
            traceback.print_exc()

    def buscar(self, query: str, top_k: int = 10, umbral_similitud: float = 0.15) -> List[Dict[str, Any]]:
        """
        Realiza búsqueda semántica
        """
        if not query.strip():
            return []
        
        print(f"Buscando con IA: '{query}'")
        
        try:
            # Generar embedding para la consulta
            query_embedding = self.gemini_client.generar_embedding(
                query, 
                task_type="RETRIEVAL_QUERY"
            )
            
            if query_embedding is None:
                return []
            
            # Normalizar query
            norma_q = np.linalg.norm(query_embedding)
            if norma_q > 0:
                query_embedding = query_embedding / norma_q
            
            # Calcular similitudes
            scores = np.dot(self.embeddings_norm, query_embedding)
            
            # Obtener mejores resultados
            top_indices = np.argsort(scores)[-top_k:][::-1]
            
            resultados = []
            for idx in top_indices:
                score = float(scores[idx])
                
                if score < umbral_similitud:
                    continue
                
                # Generar snippet resaltado
                snippet = self._generar_snippet_resaltado(
                    self.documentos[idx], 
                    query
                )
                
                resultados.append({
                    "indice": int(idx),
                    "titulo": self.titulos[idx] if idx < len(self.titulos) else "Sin título",
                    "similitud": score,
                    "snippet": snippet,
                    "abstract": self.documentos[idx][:200] + "..." if len(self.documentos[idx]) > 200 else self.documentos[idx],
                    "tipo_busqueda": "semantica_ia"
                })
            
            return resultados
            
        except Exception as e:
            print(f"Error en búsqueda IA: {e}")
            return []
    


    # En ia_busqueda.py, modifica el método obtener_recomendaciones:

    def obtener_recomendaciones(self, indice_doc: int, top_k: int = 3,
                                excluir: List[int] = None) -> List[Dict[str, Any]]:
        """
        Obtiene documentos similares usando embeddings semánticos
        CON MEJOR MANEJO DE DUPLICADOS
        """
        if excluir is None:
            excluir = []
        
        if self.sim_docs_matrix is None or indice_doc >= len(self.sim_docs_matrix):
            return []
        
        # Obtener similitudes para el documento
        similitudes = self.sim_docs_matrix[indice_doc]
        
        # Ordenar por similitud (mayor a menor)
        indices_ordenados = np.argsort(similitudes)[::-1]
        
        recomendaciones = []
        indices_vistos = set(excluir + [indice_doc])
        
        for idx in indices_ordenados:
            # Saltar si ya está en la lista de excluidos o es el documento mismo
            if idx in indices_vistos:
                continue
                
            # Limitar número de recomendaciones
            if len(recomendaciones) >= top_k:
                break
            
            # Añadir a lista de vistos para evitar duplicados futuros
            indices_vistos.add(idx)
            
            # Solo incluir si tiene similitud significativa
            if similitudes[idx] < 0.1:  # Umbral mínimo de similitud
                continue
                
            recomendaciones.append({
                "indice": int(idx),
                "titulo": self.titulos[idx] if idx < len(self.titulos) else "Sin título",
                "similitud": float(similitudes[idx]),
                "abstract": self.documentos[idx][:150] + "..." if len(self.documentos[idx]) > 150 else self.documentos[idx]
            })
        
        return recomendaciones    
    def _generar_snippet_resaltado(self, texto: str, query: str, max_longitud: int = 300) -> str:
        """
        Genera snippet con palabras de la query resaltadas
        """
        if not texto:
            return "Sin contenido disponible"
        
        tokens = normalizar_y_filtrar(query)
        texto_lower = texto.lower()
        snippets = []
        
        # Buscar ocurrencias de cada token
        for token in tokens:
            if len(token) > 2:
                pattern = re.compile(re.escape(token), re.IGNORECASE)
                matches = list(pattern.finditer(texto))
                
                for match in matches[:2]:  # Máximo 2 por token
                    start = max(0, match.start() - 50)
                    end = min(len(texto), match.end() + 50)
                    
                    snippet = texto[start:end]
                    # Resaltar
                    snippet = pattern.sub(lambda m: f"<b>{m.group(0)}</b>", snippet)
                    
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(texto):
                        snippet = snippet + "..."
                    
                    snippets.append(snippet)
        
        # Si no hay coincidencias, tomar inicio
        if not snippets:
            snippet = texto[:max_longitud]
            if len(texto) > max_longitud:
                snippet = snippet + "..."
            return snippet
        
        # Unir snippets únicos
        snippets_unicos = []
        for s in snippets:
            if s not in snippets_unicos and len(s) > 10:
                snippets_unicos.append(s)
        
        resultado = " ... ".join(snippets_unicos[:2])
        
        if len(resultado) > max_longitud:
            resultado = resultado[:max_longitud] + "..."
        
        return resultado
    
    def buscar_con_respuesta_ia(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Búsqueda que incluye respuesta generada por IA
        """
        # Primero, buscar documentos relevantes
        resultados = self.buscar(query, top_k=top_k)
        
        # Construir contexto para la IA
        contexto = "Documentos relevantes encontrados:\n\n"
        for i, res in enumerate(resultados[:3]):  # Tomar top 3 para contexto
            contexto += f"{i+1}. {res['titulo']}\n"
            contexto += f"   Resumen: {res['abstract'][:150]}...\n\n"
        
        # Generar respuesta de la IA
        respuesta_ia = self.gemini_client.consultar_chat(
            pregunta=query,
            contexto=contexto
        )
        
        return {
            "query": query,
            "respuesta_ia": respuesta_ia,
            "resultados": resultados,
            "total_resultados": len(resultados)
        }