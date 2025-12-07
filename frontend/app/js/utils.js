// utils.js - Utilidades y funciones auxiliares

// Formatear porcentaje
function formatPercentage(value) {
    return (value * 100).toFixed(1) + '%';
}

// Formatear tiempo
function formatTime(seconds) {
    if (seconds < 1) {
        return (seconds * 1000).toFixed(0) + 'ms';
    }
    return seconds.toFixed(2) + 's';
}

// Validar búsqueda
function validateQuery(query) {
    if (!query || query.trim().length === 0) {
        return { valid: false, message: 'Por favor, escribe lo que quieres buscar' };
    }
    if (query.trim().length < 2) {
        return { valid: false, message: 'La búsqueda debe tener al menos 2 caracteres' };
    }
    return { valid: true, message: '' };
}

// Escape HTML para seguridad
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Crear modal
function createModal(content, onClose = null) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.7);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
        padding: 20px;
    `;
    
    modal.innerHTML = content;
    
    // Añadir evento de cierre
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            document.body.removeChild(modal);
            if (onClose) onClose();
        }
    });
    
    document.body.appendChild(modal);
    return modal;
}

// Exportar funciones
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatPercentage,
        formatTime,
        validateQuery,
        escapeHtml,
        createModal
    };
}