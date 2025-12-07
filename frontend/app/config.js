// config.js - Configuración global
const CONFIG = {
    API_BASE: 'https://upscholar.onrender.com/api',  // Aquí sí va /api
    DEFAULT_TOP_K: 10,
    MAX_RESULTS: 50,
    ENABLE_AI: true
};

// Exportar para usar en otros archivos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}