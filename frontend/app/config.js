// config.js - Configuración dinámica
(function() {
    // Configuración por defecto para desarrollo local
    const defaultConfig = {
        API_BASE: 'http://localhost:8000',
        DEFAULT_TOP_K: 10,
        SIMILAR_TOP_K: 3
    };
    
    // Configuración de producción (se sobrescribirá por Railway)
    const productionConfig = window.RAILWAY_CONFIG || {};
    
    // Exportar configuración final
    window.CONFIG = { ...defaultConfig, ...productionConfig };
    
    console.log('Configuración cargada:', window.CONFIG);
})();