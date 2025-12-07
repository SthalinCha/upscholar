import numpy as np
import os
import pickle
import time
from typing import List, Optional
from pathlib import Path

class EmbeddingsManager:
    def __init__(self, cache_dir: str = "data/embeddings"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def guardar_embeddings(self, embeddings: np.ndarray, nombre: str = "embeddings") -> str:

        timestamp = int(time.time())
        nombre_archivo = f"{nombre}_{timestamp}.npy"
        ruta = self.cache_dir / nombre_archivo
        
        np.save(ruta, embeddings)
        
        # Guardar metadata
        metadata = {
            "fecha_creacion": timestamp,
            "dimensiones": embeddings.shape,
            "ruta": str(ruta)
        }
        
        with open(self.cache_dir / f"{nombre}_metadata.pkl", 'wb') as f:
            pickle.dump(metadata, f)
            
        print(f"✓ Embeddings guardados en: {ruta}")
        return str(ruta)
    
    def cargar_embeddings(self, nombre: str = "embeddings") -> Optional[np.ndarray]:
        """
        Carga embeddings más recientes
        """
        try:
            # Buscar archivo más reciente
            archivos_npy = list(self.cache_dir.glob(f"{nombre}_*.npy"))
            if not archivos_npy:
                return None
                
            archivo_mas_reciente = max(archivos_npy, key=os.path.getctime)
            
            print(f"✓ Cargando embeddings desde: {archivo_mas_reciente}")
            
            # Medir tiempo de carga del archivo específico
            import time
            start_time = time.time()
            
            embeddings = np.load(archivo_mas_reciente)
            
            elapsed_time = time.time() - start_time
            print(f"  Tiempo de carga del archivo {archivo_mas_reciente.name}: {elapsed_time:.3f} segundos")
            
            return embeddings
        except Exception as e:
            print(f"Error cargando embeddings: {e}")
            return None
            """
            Carga embeddings más recientes
            """
            try:
                # Buscar archivo más reciente
                archivos_npy = list(self.cache_dir.glob(f"{nombre}_*.npy"))
                if not archivos_npy:
                    return None
                    
                archivo_mas_reciente = max(archivos_npy, key=os.path.getctime)
                
                print(f"✓ Cargando embeddings desde: {archivo_mas_reciente}")
                
                # Medir tiempo de carga
                import time
                start_time = time.time()
                
                embeddings = np.load(archivo_mas_reciente)
                
                elapsed_time = time.time() - start_time
                print(f"  Tiempo de carga: {elapsed_time:.2f} segundos")
                
                return embeddings
            except Exception as e:
                print(f"Error cargando embeddings: {e}")
                return None



    def normalizar_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Normaliza embeddings para similitud coseno
        """
        if len(embeddings) == 0:
            return np.array([])
            
        normas = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normas[normas == 0] = 1
        return embeddings / normas
    
    def calcular_matriz_similitud(self, embeddings_norm: np.ndarray) -> np.ndarray:
        """
        Calcula matriz de similitud entre documentos
        """
        if len(embeddings_norm) == 0:
            return np.array([])
            
        return np.dot(embeddings_norm, embeddings_norm.T)