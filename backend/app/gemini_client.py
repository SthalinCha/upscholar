"""
Cliente para Google Gemini API
"""
import google.generativeai as genai
import time
import os
from typing import List, Optional
import numpy as np

class GeminiClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY no encontrada. Configúrala en .env o pasa como parámetro")
        
        # Configurar la API de Gemini
        genai.configure(api_key=self.api_key)
        
        # Modelos
        self.model_embedding = "models/text-embedding-004"
        self.model_chat = "models/gemini-pro"
        
    def generar_embedding(self, texto: str, task_type: str = "RETRIEVAL_DOCUMENT") -> Optional[np.ndarray]:
        """
        Genera embedding para un texto
        task_type: "RETRIEVAL_DOCUMENT" para documentos, "RETRIEVAL_QUERY" para consultas
        """
        try:
            if not texto or len(str(texto).strip()) == 0:
                texto = "documento vacio"
            
            # Usar la API actual de Gemini
            result = genai.embed_content(
                model=self.model_embedding,
                content=texto,
                task_type=task_type
            )
            
            time.sleep(0.2)  # Rate limiting
            return np.array(result['embedding'])
            
        except Exception as e:
            print(f"Error generando embedding: {e}")
            return None
    
    def generar_embeddings_lote(self, textos: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> Optional[np.ndarray]:
        """
        Genera embeddings para múltiples textos (en lotes)
        """
        embeddings = []
        
        # Medir tiempo total de generación
        import time
        start_time_total = time.time()
        
        for i, texto in enumerate(textos):
            try:
                start_doc_time = time.time()
                
                if not texto or len(str(texto).strip()) == 0:
                    texto = "documento vacio"
                
                result = genai.embed_content(
                    model=self.model_embedding,
                    content=texto,
                    task_type=task_type
                )
                
                vector = result['embedding']
                embeddings.append(vector)
                
                elapsed_doc_time = time.time() - start_doc_time
                
                # Rate limiting y progreso
                time.sleep(0.3)
                if i % 10 == 0:
                    print(f"  Embeddings generados: {i}/{len(textos)} | Último: {elapsed_doc_time:.3f}s")
                    
            except Exception as e:
                print(f"Error en documento {i}: {e}")
                # Vector cero como fallback (dimensión de embeddings de Gemini)
                embeddings.append(np.zeros(768).tolist())
        
        elapsed_total_time = time.time() - start_time_total
        print(f"✓ Tiempo total generación de embeddings con LLM: {elapsed_total_time:.2f} segundos")
        print(f"  Promedio por documento: {elapsed_total_time/len(textos):.3f} segundos")
        
        return np.array(embeddings) if embeddings else None


    def consultar_chat(self, pregunta: str, contexto: str = "") -> str:
        """
        Consulta al modelo de chat de Gemini
        """
        try:
            prompt = f"{contexto}\n\nPregunta: {pregunta}"
            
            # Crear modelo de chat
            model = genai.GenerativeModel(self.model_chat)
            response = model.generate_content(prompt)
            
            return response.text
        except Exception as e:
            print(f"Error en consulta chat: {e}")
            return f"Error en consulta: {str(e)}"