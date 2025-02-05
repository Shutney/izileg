from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from src.teste_consulta import consultar_proposicao_completa
import gradio as gr

app = FastAPI(title="izileg")

# Configura templates e arquivos estáticos
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/consulta/{pl:path}")
async def consulta(pl: str):
    try:
        resultado = consultar_proposicao_completa(pl)
        return {"status": "success", "data": resultado}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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