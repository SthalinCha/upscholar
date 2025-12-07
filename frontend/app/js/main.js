// main.js - Lógica principal de inicialización
document.addEventListener('DOMContentLoaded', function() {
    // Elementos DOM
    const searchInput = document.getElementById('search-input');
    const btnTradicional = document.getElementById('btn-tradicional');
    const btnInteligente = document.getElementById('btn-inteligente');
    const resultsContainer = document.getElementById('results-container');
    const backendStatus = document.getElementById('backend-status');
    
    // Inicializar servicios
    const api = apiService;
    const ui = uiHelper;
    
    // Verificar conexión al backend
    async function initializeBackend() {
        try {
            const health = await api.checkHealth();
            
            backendStatus.textContent = '✅ Conectado';
            backendStatus.className = 'status-online';
            
            // Mostrar mensaje inicial
            resultsContainer.innerHTML = `
                <div class="loading">
                    <p>✅ Backend conectado | ${health.documentos} documentos cargados</p>
                    <p>${health.ia_activa ? '🤖 IA disponible' : '⚠ IA no disponible'}</p>
                    <p style="margin-top:20px;">Escribe tu búsqueda y selecciona un método.</p>
                </div>
            `;
            
            return true;
            
        } catch (error) {
            backendStatus.textContent = '❌ Desconectado';
            backendStatus.className = 'status-offline';
            
            ui.showError(resultsContainer, 
                'No se pudo conectar al backend',
                `Error: ${error.message}\n\nVerifica que el backend esté ejecutándose en http://localhost:8000`
            );
            
            return false;
        }
    }
    
    // Manejador de búsqueda tradicional
    async function handleTraditionalSearch() {
        const query = searchInput.value.trim();
        const validation = validateQuery(query);
        
        if (!validation.valid) {
            alert(validation.message);
            return;
        }
        
        ui.showLoading(resultsContainer, `Buscando "${query}"...`);
        
        try {
            const results = await api.searchTraditional(query);
            ui.renderResults(resultsContainer, results, 'tradicional');
        } catch (error) {
            ui.showError(resultsContainer, 'Error en búsqueda tradicional', error.message);
            console.error('Error:', error);
        }
    }
    
    // Manejador de búsqueda con IA
    async function handleAISearch() {
        const query = searchInput.value.trim();
        const validation = validateQuery(query);
        
        if (!validation.valid) {
            alert(validation.message);
            return;
        }
        
        ui.showLoading(resultsContainer, `Buscando "${query}" con IA...`);
        
        try {
            const results = await api.searchAI(query);
            ui.renderResults(resultsContainer, results, 'inteligente');
        } catch (error) {
            ui.showError(resultsContainer, 'Error en búsqueda con IA', error.message);
            console.error('Error:', error);
        }
    }
    
    // Configurar event listeners
    function setupEventListeners() {
        btnTradicional.addEventListener('click', handleTraditionalSearch);
        btnInteligente.addEventListener('click', handleAISearch);
        
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                handleTraditionalSearch();
            }
        });
    }
    
    // Función global para ver similares (ya está en ui.js)
    window.verSimilaresModal = async function(principalIndex, tipo) {
        await ui.showSimilaresModal(principalIndex, tipo);
    };
    
    // Inicializar la aplicación
    async function initApp() {
        setupEventListeners();
        await initializeBackend();
    }
    
    // Iniciar
    initApp();
});