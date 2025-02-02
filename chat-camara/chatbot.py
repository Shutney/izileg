import gradio as gr
from teste_consulta import buscar_proposicoes, consultar_proposicao_completa
import re

def formatar_resultado(texto):
    """Formata o resultado em HTML com foco em mobile e todas as informações"""
    # Extrai as informações usando regex
    proposicao = re.search(r'Proposição: (.*?)\n', texto)
    ementa = re.search(r'Ementa: (.*?)\n', texto)
    status = re.search(r'Status: (.*?)\n', texto)
    orgao = re.search(r'Órgão atual: (.*?)\n', texto)
    orgao_nome = re.search(r'Nome completo: (.*?)\n', texto)
    orgao_tipo = re.search(r'Tipo: (.*?)\n', texto)
    data = re.search(r'Data: (.*?)\n', texto)
    despacho = re.search(r'Despacho: (.*?)\n', texto)
    descricao = re.search(r'Descrição: (.*?)\n', texto)
    regime = re.search(r'Regime de tramitação: (.*?)\n', texto)
    link_pagina = re.search(r'Página da proposição: (.*?)\n', texto)
    link_texto = re.search(r'Texto completo: (.*?)\n', texto)
    
    html = f"""
    <div style="font-family: system-ui, -apple-system, sans-serif; max-width: 800px; margin: 0 auto;">
        <div style="background-color: #004A2F; color: white; padding: 20px; border-radius: 12px 12px 0 0;">
            <h2 style="margin: 0; font-size: 1.4em; color: white;">
                {proposicao.group(1) if proposicao else ''}
            </h2>
        </div>
        
        <div style="border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 12px 12px; overflow: hidden;">
            <div style="padding: 20px; background: white;">
                <div style="font-size: 1.1em; line-height: 1.5; color: #333; margin-bottom: 20px;">
                    {ementa.group(1) if ementa else ''}
                </div>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 10px 0; color: #004A2F; font-size: 1.2em; font-weight: 600;">Situação atual</h3>
                    <div style="margin-bottom: 8px; color: #333;">
                        <strong style="color: #333;">Status:</strong> {status.group(1) if status else ''}
                    </div>
                    <div style="color: #333;">
                        <strong style="color: #333;">Órgão atual:</strong> {orgao.group(1) if orgao else ''}<br>
                        <div style="margin-left: 15px; color: #555;">
                            {orgao_nome.group(1) if orgao_nome else ''}<br>
                            {orgao_tipo.group(1) if orgao_tipo else ''}
                        </div>
                    </div>
                </div>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 10px 0; color: #004A2F; font-size: 1.2em; font-weight: 600;">Última tramitação</h3>
                    <div style="margin-bottom: 8px; color: #333;">
                        <strong style="color: #333;">Data:</strong> {data.group(1) if data else 'N/A'}
                    </div>
                    <div style="margin-bottom: 8px;">
                        <strong style="color: #333;">Despacho:</strong>
                        <div style="margin-left: 15px; color: #333; background: white; padding: 8px; border-radius: 4px; margin-top: 4px;">
                            {despacho.group(1) if despacho else 'N/A'}
                        </div>
                    </div>
                    <div>
                        <strong style="color: #333;">Descrição:</strong>
                        <div style="margin-left: 15px; color: #333; background: white; padding: 8px; border-radius: 4px; margin-top: 4px;">
                            {descricao.group(1) if descricao else 'N/A'}
                        </div>
                    </div>
                </div>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 10px 0; color: #004A2F; font-size: 1.2em; font-weight: 600;">Regime de tramitação</h3>
                    <div style="color: #333;">
                        {regime.group(1) if regime else 'N/A'}
                    </div>
                </div>
                
                <div style="border-top: 1px solid #e0e0e0; padding-top: 15px;">
                    <h3 style="margin: 0 0 10px 0; color: #004A2F; font-size: 1.2em;">Links</h3>
                    <div style="margin-bottom: 8px;">
                        <a href="{link_pagina.group(1) if link_pagina else ''}" 
                           style="color: #004A2F; text-decoration: none; display: flex; align-items: center; gap: 5px; font-weight: 500;">
                           📄 Página da proposição
                        </a>
                    </div>
                    <div>
                        <a href="{link_texto.group(1) if link_texto else ''}" 
                           style="color: #004A2F; text-decoration: none; display: flex; align-items: center; gap: 5px; font-weight: 500;">
                           📑 Texto completo
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    return html

def processar_consulta(numero_pl):
    try:
        padrao_pl = r'(PL|pl|Pl)\s*(\d+)/(\d+)'
        match = re.search(padrao_pl, numero_pl)
        
        if match:
            pl = f"{match.group(1)} {match.group(2)}/{match.group(3)}"
            resultado = consultar_proposicao_completa(pl)
            return formatar_resultado(resultado)
        else:
            return """
            <div style="padding: 15px; color: #856404; background-color: #fff3cd; border-radius: 8px;">
                ⚠️ Formato inválido. Use: PL XXXX/YYYY (exemplo: PL 2306/2020)
            </div>
            """
    except Exception as e:
        return f"""
        <div style="padding: 15px; color: #721c24; background-color: #f8d7da; border-radius: 8px;">
            ❌ Erro: {str(e)}
        </div>
        """

with gr.Blocks(
    title="Consulta de Proposições",
    css="""
        /* Reset e configurações gerais */
        * { box-sizing: border-box; }
        
        .gradio-container { 
            max-width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
            background-color: #f5f5f5 !important;
        }
        
        /* Header */
        .header {
            background-color: #004A2F !important;
            padding: 1rem !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        }
        
        /* Campo de busca */
        .input-row { 
            background: white !important;
            padding: 15px !important;
            margin: 15px !important;
            border-radius: 8px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
        }
        
        /* Botões */
        .button-row { 
            padding: 0 15px 15px 15px !important;
            display: flex !important;
            gap: 10px !important;
        }
        
        /* Área de resultado */
        .result-row { 
            padding: 0 15px 15px 15px !important;
        }
        
        /* Estilo dos botões */
        button.primary {
            background-color: #004A2F !important;
            color: white !important;
            border: none !important;
            padding: 10px 20px !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            transition: background-color 0.2s !important;
        }
        
        button.primary:hover {
            background-color: #006241 !important;
        }
        
        button.secondary {
            background-color: #f5f5f5 !important;
            color: #333 !important;
            border: 1px solid #ddd !important;
            padding: 10px 20px !important;
            border-radius: 6px !important;
        }
        
        /* Campo de texto */
        input[type="text"] {
            border: 2px solid #e0e0e0 !important;
            border-radius: 6px !important;
            padding: 12px !important;
            font-size: 1.1em !important;
            width: 100% !important;
            transition: border-color 0.2s !important;
        }
        
        input[type="text"]:focus {
            border-color: #004A2F !important;
            outline: none !important;
        }
        
        /* Placeholder */
        input[type="text"]::placeholder {
            color: #666 !important;
            opacity: 0.8 !important;
        }
    """
) as iface:
    gr.HTML("""
    <div class="header" style="text-align: center;">
        <h2 style="margin: 0; font-weight: 600; font-size: 1.4em; color: white;">Consulta de Proposições</h2>
        <p style="margin: 5px 0 0 0; color: rgba(255,255,255,0.9); font-size: 0.9em;">Câmara dos Deputados</p>
    </div>

    <div style="padding: 15px; margin: 15px; background: white; border-radius: 8px; border-left: 4px solid #004A2F;">
        <p style="margin: 0; color: #333; font-size: 0.95em;">
            <strong style="color: #004A2F;">Como usar:</strong> Digite o número da proposição no formato "PL XXXX/YYYY" 
            (exemplo: PL 2306/2020) e clique em Consultar ou pressione Enter.
        </p>
    </div>
    """)
    
    with gr.Column():
        with gr.Row(elem_classes="input-row"):
            numero = gr.Textbox(
                placeholder="Digite o número da proposição (exemplo: PL 2306/2020)",
                label="",
                container=False,
            )
        
        with gr.Row(elem_classes="button-row"):
            consultar = gr.Button("Consultar", variant="primary", size="lg", elem_classes="primary")
            limpar = gr.Button("Limpar", variant="secondary", size="lg", elem_classes="secondary")
        
        with gr.Row(elem_classes="result-row"):
            resultado = gr.HTML()
        
        consultar.click(
            processar_consulta,
            inputs=[numero],
            outputs=[resultado],
        )
        
        limpar.click(
            lambda: ("", ""),
            outputs=[numero, resultado],
        )
        
        numero.submit(
            processar_consulta,
            inputs=[numero],
            outputs=[resultado],
        )

app = gr.mount_gradio_app(None, iface, path="/")

if __name__ == "__main__":
    iface.launch(
        server_port=7861,
        show_error=True,
        share=False
    ) 