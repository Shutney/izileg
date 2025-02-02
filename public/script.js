async function consultarProposicao() {
    const input = document.getElementById('proposicao').value;
    const resultado = document.getElementById('resultado');
    
    try {
        // Extrai número e ano
        const match = input.match(/PL\s*(\d+)\/(\d+)/i);
        if (!match) {
            throw new Error('Formato inválido. Use: PL XXXX/YYYY (exemplo: PL 2306/2020)');
        }

        const [_, numero, ano] = match;
        
        // Consulta a API da Câmara
        const response = await fetch(`https://dadosabertos.camara.leg.br/api/v2/proposicoes?siglaTipo=PL&numero=${numero}&ano=${ano}`);
        const data = await response.json();
        
        if (!data.dados || data.dados.length === 0) {
            throw new Error('Proposição não encontrada');
        }

        const prop = data.dados[0];
        const id = prop.id;

        // Busca detalhes da tramitação
        const [detalhesRes, tramitacoesRes] = await Promise.all([
            fetch(`https://dadosabertos.camara.leg.br/api/v2/proposicoes/${id}`),
            fetch(`https://dadosabertos.camara.leg.br/api/v2/proposicoes/${id}/tramitacoes`)
        ]);

        const detalhes = await detalhesRes.json();
        const tramitacoes = await tramitacoesRes.json();

        const dadosFormatados = {
            proposicao: `${prop.siglaTipo} ${prop.numero}/${prop.ano}`,
            ementa: prop.ementa,
            status: detalhes.dados.statusProposicao.descricaoSituacao,
            orgao: detalhes.dados.statusProposicao.siglaOrgao,
            data: tramitacoes.dados[0]?.dataHora || 'N/A',
            despacho: tramitacoes.dados[0]?.despacho || 'N/A',
            descricao: tramitacoes.dados[0]?.descricaoTramitacao || 'N/A',
            regime: detalhes.dados.statusProposicao.regime,
            link_pagina: `https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao=${id}`,
            link_texto: detalhes.dados.urlInteiroTeor
        };

        resultado.innerHTML = formatarResultado(dadosFormatados);
    } catch (error) {
        resultado.innerHTML = `
            <div class="card" style="border-color: #dc3545;">
                <div class="card-body">
                    <p style="color: #dc3545;">${error.message}</p>
                </div>
            </div>
        `;
    }
}

function formatarResultado(data) {
    return `
        <div class="card">
            <div class="card-header">
                <h2>${data.proposicao}</h2>
            </div>
            <div class="card-body">
                <p>${data.ementa}</p>
                
                <div class="info-section">
                    <h3>Situação atual</h3>
                    <p><strong>Status:</strong> ${data.status}</p>
                    <p><strong>Órgão atual:</strong> ${data.orgao}</p>
                    <p>${data.orgao_nome}</p>
                    <p>${data.orgao_tipo}</p>
                </div>
                
                <div class="info-section">
                    <h3>Última tramitação</h3>
                    <p><strong>Data:</strong> ${data.data}</p>
                    <p><strong>Despacho:</strong> ${data.despacho}</p>
                    <p><strong>Descrição:</strong> ${data.descricao}</p>
                </div>
                
                <div class="info-section">
                    <h3>Regime de tramitação</h3>
                    <p>${data.regime}</p>
                </div>
                
                <div style="margin-top: 1rem;">
                    <p><a href="${data.link_pagina}" target="_blank">📄 Página da proposição</a></p>
                    <p><a href="${data.link_texto}" target="_blank">📑 Texto completo</a></p>
                </div>
            </div>
        </div>
    `;
} 