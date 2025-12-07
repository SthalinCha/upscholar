// api.js - Funciones de comunicación con la API
class ApiService {
    constructor(baseUrl = CONFIG.API_BASE) {
        this.baseUrl = baseUrl;
    }

    // Verificar salud del backend
    async checkHealth() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            if (response.ok) {
                return await response.json();
            }
            throw new Error(`HTTP ${response.status}`);
        } catch (error) {
            console.error('Health check failed:', error);
            throw error;
        }
    }

    // Búsqueda tradicional - YA INCLUYE RECOMENDACIONES
    async searchTraditional(query, topK = CONFIG.DEFAULT_TOP_K) {
        const response = await fetch(`${this.baseUrl}/buscar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                texto: query, 
                top_k: topK
            })
        });
        
        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }

    // Búsqueda con IA - YA INCLUYE RECOMENDACIONES
    async searchAI(query, topK = CONFIG.DEFAULT_TOP_K) {
        const response = await fetch(`${this.baseUrl}/buscar-ia`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                texto: query, 
                top_k: topK
            })
        });
        
        if (!response.ok) {
            if (response.status === 503) {
                throw new Error('La búsqueda con IA no está disponible. Configura GOOGLE_API_KEY en el backend.');
            }
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }

    // Obtener documento completo
    async getDocument(index) {
        const response = await fetch(`${this.baseUrl}/documento/${index}`);
        if (!response.ok) throw new Error('Documento no encontrado');
        return await response.json();
    }

    // Obtener recomendaciones - AHORA SE FILTRAN DE LOS RESULTADOS YA RECIBIDOS
    async getRecommendations(index, type = 'tradicional', topK = 3) {
        // Este método ya no llama al backend, solo filtra de los resultados existentes
        // Pero necesitamos guardar los resultados en algún lugar
        return {
            recomendaciones: [],
            documento_referencia: null
        };
    }

    // Verificar estado de IA
    async checkAIStatus() {
        const response = await fetch(`${this.baseUrl}/status-ia`);
        if (response.ok) {
            return await response.json();
        }
        throw new Error('Error al verificar estado de IA');
    }
}

// Crear instancia global
const apiService = new ApiService();

// Exportar para usar en otros archivos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ApiService;
}