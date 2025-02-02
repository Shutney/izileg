from fastapi import FastAPI, HTTPException
from teste_consulta import consultar_proposicao_completa
import re

app = FastAPI()

@app.post("/api/consulta")
async def consulta(data: dict):
    try:
        proposicao = data.get("proposicao", "")
        resultado = consultar_proposicao_completa(proposicao)
        return parse_resultado(resultado)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def parse_resultado(texto):
    # Função para extrair as informações do texto e retornar um JSON
    # ... (implementar parser) 