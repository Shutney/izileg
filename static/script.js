async function consultarPL() {
    const input = document.getElementById('pl-input');
    const resultado = document.getElementById('resultado');
    const pl = input.value.trim();

    if (!pl) {
        resultado.innerHTML = '<div class="error">Digite o número da proposição</div>';
        return;
    }

    try {
        resultado.innerHTML = '<div class="loading">Consultando...</div>';
        // Remove espaços extras e formata a URL
        const plFormatado = pl.replace(/\s+/g, ' ').trim();
        const response = await fetch(`/consulta/${encodeURIComponent(plFormatado)}`);
        const data = await response.json();

        if (data.status === 'success') {
            resultado.innerHTML = formatarResultado(data.data);
        } else {
            resultado.innerHTML = `<div class="error">${data.message}</div>`;
        }
    } catch (error) {
        resultado.innerHTML = '<div class="error">Erro ao consultar proposição</div>';
    }
}

function formatarResultado(texto) {
    // Formata seções especiais
    texto = texto
        .replace(/\[TITULO\](.*?)\[\/TITULO\]/g, '<h2 class="resultado-titulo">$1</h2>')
        .replace(/\[SUBTITULO\](.*?)\[\/SUBTITULO\]/g, '<h3 class="resultado-subtitulo">$1</h3>')
        .replace(/\[INFO\](.*?)\[\/INFO\]/g, '<div class="info-box">$1</div>')
        .replace(/\[LINKS\](.*?)\[\/LINKS\]/g, '<div class="links-container">$1</div>')
        .replace(/\[LINK_PAGINA\](.*?)\[\/LINK_PAGINA\]/g, '<a href="$1" target="_blank" class="link-proposicao">📄 Página da proposição</a>')
        .replace(/\[LINK_TEXTO\](.*?)\[\/LINK_TEXTO\]/g, '<a href="$1" target="_blank" class="link-texto">📑 Texto completo</a>');
    
    // Formata o resto do texto
    return texto
        .replace(/\n/g, '<br>')
        .replace(/•\s([^:]+):/g, '<span class="item">$1:</span>');
}

// Permite consultar ao pressionar Enter
document.getElementById('pl-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        consultarPL();
    }
}); 