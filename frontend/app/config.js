const CONFIG = {
    API_BASE: 'https://upscholar.onrender.com',  // URL completa de tu backend en Render
    DEFAULT_TOP_K: 10,
    MAX_RESULTS: 50,
    ENABLE_AI: true
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}
