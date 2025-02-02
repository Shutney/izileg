import gradio as gr
from teste_consulta import buscar_proposicoes, consultar_proposicao_completa
import re

def processar_pergunta(pergunta):
    """
    Processa a pergunta do usuário e retorna uma resposta apropriada
    """
    # Padrões comuns de perguntas
    padrao_pl = r'(PL|pl|Pl)\s*(\d+)/(\d+)'  # Busca PL XXXX/YYYY
    padrao_numero = r'(\d+)/(\d+)'           # Busca XXXX/YYYY
    padrao_situacao = r'(como|qual|onde).*(está|anda|tramita|situação).*?(PL|pl|Pl)\s*(\d+)/(\d+)'
    
    try:
        # Verifica se é pergunta sobre situação
        if re.search(padrao_situacao, pergunta):
            match = re.search(padrao_pl, pergunta)
            if match:
                pl = f"{match.group(1)} {match.group(2)}/{match.group(3)}"
                return consultar_proposicao_completa(pl)
            
        # Verifica se é busca direta por PL
        elif re.search(padrao_pl, pergunta):
            match = re.search(padrao_pl, pergunta)
            pl = f"{match.group(1)} {match.group(2)}/{match.group(3)}"
            resultados = buscar_proposicoes(pl)
            if resultados:
                return consultar_proposicao_completa(pl)
            
        # Verifica se é busca por número
        elif re.search(padrao_numero, pergunta):
            match = re.search(padrao_numero, pergunta)
            numero = f"{match.group(1)}/{match.group(2)}"
            resultados = buscar_proposicoes(numero)
            if resultados:
                resposta = "Encontrei os seguintes resultados:\n\n"
                for i, res in enumerate(resultados, 1):
                    resposta += f"{i}. {res['titulo']}\n"
                    resposta += f"Link: {res['link']}\n\n"
                return resposta
            
        # Busca por termo
        else:
            resultados = buscar_proposicoes(pergunta)
            if resultados:
                resposta = "Encontrei os seguintes resultados:\n\n"
                for i, res in enumerate(resultados, 1):
                    resposta += f"{i}. {res['titulo']}\n"
                    resposta += f"Link: {res['link']}\n\n"
                return resposta
        
        return "Desculpe, não encontrei nenhuma proposição com esses critérios. Tente reformular sua pergunta."
    
    except Exception as e:
        return f"Desculpe, ocorreu um erro: {str(e)}"

# Cria a interface do chatbot
iface = gr.Interface(
    fn=processar_pergunta,
    inputs=gr.Textbox(
        placeholder="Digite sua pergunta... (ex: 'Como está o PL 2306/2020?' ou 'Buscar PL sobre meio ambiente')"
    ),
    outputs="text",
    title="Chatbot da Câmara",
    description="""
    Este chatbot pode ajudar você a:
    - Buscar proposições por número (ex: "2306/2020")
    - Buscar PLs específicos (ex: "PL 2306/2020")
    - Verificar a situação de PLs (ex: "Como está o PL 2306/2020?")
    - Buscar por tema (ex: "projetos sobre meio ambiente")
    """,
    examples=[
        ["Como está o PL 2306/2020?"],
        ["PL 2752/2024"],
        ["2405/2021"],
        ["projetos sobre meio ambiente"],
    ]
)

if __name__ == "__main__":
    iface.launch() 