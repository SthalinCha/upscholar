// ui.js - Funciones de renderizado/interfaz
class UIHelper {
    constructor() {
        this.currentResults = null;
        this.apiService = apiService;
    }

    // Mostrar estado de carga
    showLoading(container, message = 'Procesando...') {
        container.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p>${message}</p>
            </div>
        `;
    }

    // Mostrar error
    showError(container, message, details = '') {
        container.innerHTML = `
            <div class="error">
                <p>${message}</p>
                ${details ? `<p><small>${details}</small></p>` : ''}
                <button onclick="location.reload()" class="action-btn" style="margin-top:10px;">
                    Reintentar
                </button>
            </div>
        `;
    }

    // Renderizar resultados - SOLO PRINCIPALES
    renderResults(container, data, type) {
        this.currentResults = data;
        
        let html = '';
        
        // Cabecera con estadísticas
        html += `
            <div class="results-header">
                <h3>${type === 'inteligente' ? ' Resultados IA' : ' Resultados Tradicionales'}</h3>
                <div class="search-stats">
                    
                    <span> ${data.estadisticas?.principales || 10} artículos principales</span>
                    <span>⏱️ ${data.tiempo || '0.0'}s</span>
                    
                </div>
            </div>
        `;
        
        // Separar principales y adicionales
        const resultados = data.resultados || [];
        const principales = [];
        const adicionalesPorPrincipal = {};
        
        resultados.forEach(item => {
            if (item.es_principal || item.ranking !== undefined || item.principal_relacionado === undefined) {
                principales.push(item);
            } else if (item.principal_relacionado !== undefined) {
                // Agrupar adicionales por su artículo principal
                if (!adicionalesPorPrincipal[item.principal_relacionado]) {
                    adicionalesPorPrincipal[item.principal_relacionado] = [];
                }
                adicionalesPorPrincipal[item.principal_relacionado].push(item);
            }
        });
        
        // Mostrar solo los artículos principales (máximo 10)
        const principalesLimitados = principales.slice(0, 10);
        
        if (principalesLimitados.length > 0) {
            principalesLimitados.forEach((principal, index) => {
                // Calcular ranking (empezando desde 1)
                const ranking = index + 1;
                
                html += this.renderPrincipalItem(principal, type, ranking, adicionalesPorPrincipal);
            });
        } else {
            html += `
                <div class="no-results">
                    <p>No se encontraron resultados para tu búsqueda.</p>
                    <p>Intenta con otros términos o prueba la búsqueda inteligente.</p>
                </div>
            `;
        }
        
        container.innerHTML = html;
    }

    // Renderizar artículo principal CON botón para modal de similares
    renderPrincipalItem(principal, tipo, ranking, adicionalesPorPrincipal) {
        const similitudPorcentaje = formatPercentage(principal.similitud);
        const iconoTipo = tipo === 'inteligente' ? '' : '';
        const similaresDisponibles = adicionalesPorPrincipal[principal.indice] || [];
        const tieneSimilares = similaresDisponibles.length > 0;
        
        return `
            <div class="result-item principal-item">
                
                <div class="result-header">
                    <div class="result-title" onclick="verDocumento(${principal.indice})">
                        ${iconoTipo} ${principal.titulo || 'Sin título'}
                    </div>
                    <div class="result-similarity-badge">
                        ${similitudPorcentaje} relevante
                    </div>
                </div>
                
                <div class="result-snippet">
                    ${principal.snippet || 'Sin descripción disponible...'}
                </div>
                
                <div class="result-footer">
                    <div class="result-meta">
                        <span>📄 Documento #${principal.indice}</span>
                        <span>${tipo === 'inteligente' ? 'Gemini AI' : 'TF-IDF'}</span>
                    </div>
                    
                    <div class="result-actions">
                        <button class="action-btn" onclick="verDocumento(${principal.indice})">
                            📖 Ver completo
                        </button>
                        ${tieneSimilares ? `
                            <button class="action-btn btn-similares" 
                                    onclick="verSimilaresModal(${principal.indice}, '${tipo}')">
                                🔗 Ver 3 similares
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    // Mostrar documento en modal
    async showDocument(index) {
        try {
            const data = await this.apiService.getDocument(index);
            
            const modalContent = `
                <div style="background: white; border-radius: 10px; padding: 30px; max-width: 800px; max-height: 80vh; overflow-y: auto; position: relative;">
                    <button onclick="this.parentElement.parentElement.remove()" style="position: absolute; top: 10px; right: 10px; background: #d93025; color: white; border: none; border-radius: 50%; width: 30px; height: 30px; cursor: pointer;">×</button>
                    <h2 style="color: #1a73e8; margin-bottom: 15px;">${data.titulo}</h2>
                    <div style="margin-bottom: 15px; color: #666; font-size: 0.9rem;">
                        <strong>📄 Documento #   ${data.indice}</strong>
                    </div>
                    <div style="line-height: 1.8; color: #333;">
                        <h4 style="margin-bottom: 10px; color: #555;">Abstract:</h4>
                        <p style="white-space: pre-wrap;">${data.abstract_completo || data.abstract}</p>
                    </div>
                </div>
            `;
            
            createModal(modalContent);
            
        } catch (error) {
            alert('Error al cargar el documento: ' + error.message);
        }
    }

    // Mostrar similares en modal
    async showSimilaresModal(principalIndex, tipo) {
        try {
            // Buscar el artículo principal y sus similares en los resultados actuales
            const resultados = this.currentResults.resultados || [];
            
            // Encontrar el artículo principal
            const principal = resultados.find(item => 
                item.indice === principalIndex && 
                (item.es_principal || item.ranking !== undefined)
            );
            
            // Encontrar los similares de este artículo principal
            const similares = resultados.filter(item => 
                item.principal_relacionado === principalIndex
            );
            
            if (!principal) {
                alert('No se encontró el artículo principal');
                return;
            }
            
            let similaresHTML = '';
            
            if (similares.length > 0) {
                similares.forEach((similar, index) => {
                    const similitudPorcentaje = formatPercentage(similar.similitud);
                    
                    similaresHTML += `
                        <div style="
                            background: #f8f9fa; 
                            padding: 20px;
                            border-radius: 10px;
                            margin-bottom: 15px;
                            border-left: 5px solid #34a853;
                            transition: all 0.3s ease;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                        " onmouseover="this.style.boxShadow='0 4px 12px rgba(0,0,0,0.1)'; this.style.transform='translateY(-2px)'"
                        onmouseout="this.style.boxShadow='0 2px 8px rgba(0,0,0,0.05)'; this.style.transform='translateY(0)'">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                <div>
                                    <div style="
                                        font-weight: 600; 
                                        margin-bottom: 8px; 
                                        color: #1a0dab; 
                                        cursor: pointer; 
                                        font-size: 18px;
                                        line-height: 1.4;
                                    " onclick="verDocumento(${similar.indice})">
                                        ${similar.titulo || 'Sin título'}
                                    </div>
                                    <div style="
                                        color: #555;
                                        font-size: 15px;
                                        margin-bottom: 12px; 
                                        line-height: 1.6;
                                    ">
                                        ${similar.snippet?.substring(0, 200) || 'Sin descripción disponible'}...
                                    </div>
                                </div>
                                <div style="
                                    color: #34a853; 
                                    font-weight: bold;
                                    background: rgba(52, 168, 83, 0.1);
                                    padding: 8px 15px;
                                    border-radius: 15px;
                                    font-size: 16px;
                                ">
                                    ${similitudPorcentaje} similar
                                </div>
                            </div>
                            <div style="
                                display: flex; 
                                justify-content: space-between; 
                                font-size: 14px;
                                color: #5f6368; 
                                padding-top: 10px;
                                border-top: 1px solid #e8eaed;
                                margin-top: 10px;
                            ">
                                <span style="display: flex; align-items: center; gap: 5px;">
                                    📄 Documento #${similar.indice}
                                </span>
                                <div>
                                    <button style="
                                        padding: 8px 16px;
                                        background: #1a73e8;
                                        color: white;
                                        border: none;
                                        border-radius: 6px;
                                        cursor: pointer;
                                        font-weight: 500;
                                        transition: all 0.2s;
                                    " onmouseover="this.style.background='#0d62c9'"
                                    onmouseout="this.style.background='#1a73e8'"
                                    onclick="verDocumento(${similar.indice})">
                                        📖 Ver documento completo
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                });
            } else {
                similaresHTML = `
                    <div style="text-align: center; padding: 40px 20px; color: #666;">
                        <p style="font-size: 18px; margin-bottom: 10px;">😕 No hay artículos similares disponibles</p>
                        <p>Este artículo no tiene recomendaciones similares en la base de datos.</p>
                    </div>
                `;
            }
            
            const modalContent = `
                <div style="background: white; border-radius: 10px; padding: 30px; max-width: 900px; max-height: 85vh; overflow-y: auto; position: relative;">
                    <button onclick="this.parentElement.parentElement.remove()" style="position: absolute; top: 15px; right: 15px; background: #d93025; color: white; border: none; border-radius: 50%; width: 35px; height: 35px; cursor: pointer; font-size: 20px; display: flex; align-items: center; justify-content: center;">×</button>
                    
                    <div style="margin-bottom: 25px;">
                        <h2 style="color: #1a73e8; margin-bottom: 10px; font-size: 24px;">
                            🔗 Artículos similares
                        </h2>
                        <div style="background: #f0f7ff; padding: 15px; border-radius: 8px; border-left: 4px solid #1a73e8;">
                            <div style="font-weight: 600; font-size: 18px; color: #1a0dab; margin-bottom: 5px;">
                                ${principal.titulo || 'Artículo de referencia'}
                            </div>
                            <div style="color: #666; font-size: 14px;">
                                📄 Documento #${principal.indice} • 
                                ${formatPercentage(principal.similitud)} relevante •
                                ${tipo === 'inteligente' ? ' Gemini AI' : ' TF-IDF'}
                            </div>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 20px;">
                        <h3 style="color: #34a853; font-size: 20px; margin-bottom: 15px;">
                            📚 Artículos relacionados
                        </h3>
                        <div style="max-height: 500px; overflow-y: auto; padding-right: 10px;">
                            ${similaresHTML}
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin-top: 25px; padding-top: 20px; border-top: 1px solid #eee;">
                        <p style="color: #666; font-size: 14px;">
                            Estos artículos son similares en contenido al documento de referencia.
                        </p>
                    </div>
                </div>
            `;
            
            createModal(modalContent);
            
        } catch (error) {
            console.error('Error al mostrar similares:', error);
            alert('Error al cargar los artículos similares: ' + error.message);
        }
    }
}

// Crear instancia global
const uiHelper = new UIHelper();

// Funciones globales para usar en atributos onclick
window.verDocumento = async (index) => await uiHelper.showDocument(index);
window.verSimilaresModal = async (principalIndex, tipo) => await uiHelper.showSimilaresModal(principalIndex, tipo);

// Exportar para usar en otros archivos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UIHelper;
}