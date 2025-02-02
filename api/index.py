from fastapi import FastAPI
from teste_consulta import buscar_proposicoes, consultar_proposicao_completa
import gradio as gr

app = FastAPI()

# ... resto do código do chatbot ...

iface = gr.Interface(
    fn=processar_consulta,
    inputs=gr.Textbox(
        placeholder="Digite o número da proposição (exemplo: PL 2306/2020)",
        label="",
    ),
    outputs=gr.HTML(),
    title="Consulta de Proposições",
    description="Digite o número da proposição (exemplo: PL 2306/2020)",
    theme=gr.themes.Base()
)

app = gr.mount_gradio_app(app, iface, path="/") 