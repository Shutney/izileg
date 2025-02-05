import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

# Lista completa de tipos comuns
TIPOS_PROPOSICOES = [
    'PL',   # Projeto de Lei
    'PLP',  # Projeto de Lei Complementar
    'PEC',  # Proposta de Emenda à Constituição
    'MPV',  # Medida Provisória
    'PDL',  # Projeto de Decreto Legislativo
    'PRC',  # Projeto de Resolução
    'REQ',  # Requerimento
    'INC',  # Indicação
    'RIC',  # Requerimento de Informação
    'PDC',  # Projeto de Decreto Legislativo
]

def buscar_proposicoes(termo):
    """
    Busca proposições na API da Câmara
    """
    try:
        # Remove espaços extras e formata o termo
        termo = termo.strip()
        
        # Se for apenas números e barra (ex: "2306/2020")
        if re.match(r'^\d+/\d+$', termo):
            numero, ano = termo.split('/')
            resultados = []
            for tipo in TIPOS_PROPOSICOES:
                url = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"
                params = {
                    'siglaTipo': tipo,
                    'numero': numero,
                    'ano': ano
                }
                response = requests.get(url, params=params)
                dados = response.json()['dados']
                if dados:
                    resultados.append({
                        'titulo': f"{dados[0]['siglaTipo']} {dados[0]['numero']}/{dados[0]['ano']}",
                        'id': dados[0]['id'],
                        'link': f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={dados[0]['id']}"
                    })
            return resultados
            
        # Se já vier com o tipo (ex: "PL 2306/2020")
        elif ' ' in termo:
            sigla, numero_ano = termo.split(' ')
            numero, ano = numero_ano.split('/')
            url = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"
            params = {
                'siglaTipo': sigla.upper(),
                'numero': numero,
                'ano': ano
            }
            response = requests.get(url, params=params)
            dados = response.json()['dados']
            if dados:
                return [{
                    'titulo': f"{dados[0]['siglaTipo']} {dados[0]['numero']}/{dados[0]['ano']}",
                    'id': dados[0]['id'],
                    'link': f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={dados[0]['id']}"
                }]
        
        return []
        
    except Exception as e:
        print(f"Erro ao buscar proposições: {str(e)}")
        return []

def formatar_erro_busca():
    return """
[TITULO]Como pesquisar proposições[/TITULO]

[INFO]
Digite o tipo e número da proposição ou apenas o número para ver todas as opções.

Exemplos de busca:
• PL 2306/2020 (Projeto de Lei)
• PEC 45/2019 (Proposta de Emenda à Constituição)
• REQ 123/2024 (Requerimento)
• MPV 1172/2023 (Medida Provisória)
• 2306/2020 (busca em todos os tipos)

Tipos disponíveis:
• PL  - Projeto de Lei
• PLP - Projeto de Lei Complementar
• PEC - Proposta de Emenda à Constituição
• MPV - Medida Provisória
• PDL - Projeto de Decreto Legislativo
• PRC - Projeto de Resolução
• REQ - Requerimento
• INC - Indicação
• RIC - Requerimento de Informação
[/INFO]
"""

def consultar_proposicao_completa(pl):
    """
    Consulta detalhes completos de uma proposição
    """
    try:
        resultados = buscar_proposicoes(pl)
        if not resultados:
            return formatar_erro_busca()
        
        if len(resultados) > 1:
            # Formata múltiplos resultados
            resposta = "[TITULO]Proposições encontradas[/TITULO]\n"
            resposta += "Encontramos várias proposições com este número:\n\n"
            for res in resultados:
                resposta += f"• {res['titulo']}\n"
            resposta += "\nPor favor, especifique o tipo (ex: PL, PEC, etc)"
            return resposta
            
        id_prop = resultados[0]['id']
        
        # Consulta detalhes via API
        url = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes/{id_prop}"
        response = requests.get(url)
        prop = response.json()['dados']
        
        # Consulta órgão atual
        orgao_atual = None
        if 'statusProposicao' in prop and 'siglaOrgao' in prop['statusProposicao']:
            response = requests.get("https://dadosabertos.camara.leg.br/api/v2/orgaos", 
                                 params={'sigla': prop['statusProposicao']['siglaOrgao']})
            orgaos = response.json()['dados']
            if orgaos:
                orgao_atual = orgaos[0]
        
        # Consulta tramitações
        url_tram = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes/{id_prop}/tramitacoes"
        response = requests.get(url_tram)
        trams = response.json()['dados']
        
        # Ordena tramitações por data mais recente
        trams.sort(key=lambda x: x['dataHora'], reverse=True)
        ultima_tramitacao = trams[0] if trams else None
        
        # Busca autores
        url_autores = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes/{id_prop}/autores"
        response = requests.get(url_autores)
        autores = response.json()['dados']
        
        # Processa autores
        autores_info = []
        
        for i, autor in enumerate(autores):
            if i >= 2:  # Se tiver mais de 2 autores
                autores_info.append("e outros")
                break
                
            nome_autor = autor.get('nome', 'N/A')
            partido_uf = "N/A"
            
            # Busca partido/UF de cada autor
            if autor.get('uri'):
                id_deputado = autor['uri'].split('/')[-1]
                url_deputado = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{id_deputado}"
                response = requests.get(url_deputado)
                if response.status_code == 200:
                    deputado = response.json()['dados']
                    ultimo_status = deputado.get('ultimoStatus', {})
                    partido = ultimo_status.get('siglaPartido', '')
                    uf = ultimo_status.get('siglaUf', '')
                    if partido and uf:
                        partido_uf = f"{partido}/{uf}"
            
            autores_info.append(f"{nome_autor} ({partido_uf})")
        
        # Formata os autores com seus respectivos partidos/UF
        autores_formatado = ", ".join(autores_info)
        
        # Formata a resposta
        resposta = f"""
[TITULO]{prop['siglaTipo']} {prop['numero']}/{prop['ano']}[/TITULO]
{prop['ementa']}

[SUBTITULO]Informações[/SUBTITULO]
• Autor{'es' if len(autores_info) > 1 else 'a' if 'Deputada' in autores[0].get('nome', '') else ''}: {autores_formatado}
• Status: {prop['statusProposicao']['descricaoSituacao']}
• Órgão: {prop['statusProposicao']['siglaOrgao']} - {orgao_atual['nome'] if orgao_atual else 'N/A'}
• Regime: {prop['statusProposicao']['regime']}

[SUBTITULO]Última atualização[/SUBTITULO]
{datetime.strptime(ultima_tramitacao['dataHora'], '%Y-%m-%dT%H:%M').strftime('%d/%m/%Y às %H:%M') if ultima_tramitacao else 'N/A'}
{ultima_tramitacao['despacho'] if ultima_tramitacao else 'N/A'}

[SUBTITULO]Links[/SUBTITULO]
Página da proposição: <a href="{resultados[0]['link']}" target="_blank">{resultados[0]['link']}</a>
Texto completo: <a href="{prop.get('urlInteiroTeor', '#')}" target="_blank">{prop.get('urlInteiroTeor', 'N/A')}</a>
"""
        return resposta
        
    except Exception as e:
        return f"Erro ao consultar proposição: {str(e)}"

def consultar_tramitacao_web(id_proposicao):
    """
    Consulta a página web de tramitação de uma proposição
    """
    url = f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={id_proposicao}"
    
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Busca a tabela de tramitação
        tabela_tramitacao = soup.find('table', {'id': 'content-tramitacao'}) or \
                           soup.find('table', class_='table')
        
        tramitacoes = []
        if tabela_tramitacao:
            for linha in tabela_tramitacao.find_all('tr')[1:]:  # Pula o cabeçalho
                colunas = linha.find_all('td')
                if len(colunas) >= 3:
                    data_str = colunas[0].text.strip()
                    try:
                        # Converte data para ordenação
                        data_obj = datetime.strptime(data_str, '%d/%m/%Y')
                        data = data_str
                    except:
                        data_obj = datetime.min
                        data = data_str
                    
                    orgao = colunas[1].text.strip()
                    despacho = colunas[2].text.strip()
                    
                    tramitacoes.append({
                        'data': data,
                        'data_obj': data_obj,
                        'orgao': orgao,
                        'despacho': despacho
                    })
        
        # Ordena tramitações por data mais recente
        tramitacoes.sort(key=lambda x: x['data_obj'], reverse=True)
        
        # Formata a resposta apenas se tiver informações adicionais
        resposta = ""
        if tramitacoes:
            resposta += "\nHistórico de tramitações:"
            for tram in tramitacoes[:5]:  # Mostra as 5 mais recentes
                resposta += f"\n\n📅 {tram['data']}"
                resposta += f"\n📍 {tram['orgao']}"
                if tram['despacho'].strip():
                    resposta += f"\n📝 {tram['despacho']}"
                resposta += "\n---"
        
        return resposta if resposta else ""
        
    except Exception as e:
        print(f"Erro ao consultar página web: {str(e)}")  # Debug
        return ""

def consultar_proposicao(id_ou_sigla):
    """
    Consulta detalhes de uma proposição específica.
    """
    base_url = "https://dadosabertos.camara.leg.br/api/v2"
    
    try:
        # Se receber uma sigla (ex: PL 1234/2023), precisa converter para ID
        if isinstance(id_ou_sigla, str):
            sigla_tipo, numero_ano = id_ou_sigla.split(' ')
            numero, ano = numero_ano.split('/')
            
            # Busca a proposição pelo tipo, número e ano
            params = {
                'siglaTipo': sigla_tipo,
                'numero': numero,
                'ano': ano
            }
            response = requests.get(f"{base_url}/proposicoes", params=params)
            dados = response.json()['dados']
            if not dados:
                return "Proposição não encontrada"
            id_prop = dados[0]['id']
        else:
            id_prop = id_ou_sigla
        
        # Busca detalhes da proposição
        response = requests.get(f"{base_url}/proposicoes/{id_prop}")
        prop = response.json()['dados']
        
        # Busca tramitações
        response = requests.get(f"{base_url}/proposicoes/{id_prop}/tramitacoes")
        trams = response.json()['dados']
        
        # Ordena tramitações por data
        for tram in trams:
            try:
                data_obj = datetime.strptime(tram['dataHora'].split('T')[0], '%Y-%m-%d')
                tram['data_obj'] = data_obj
            except:
                tram['data_obj'] = datetime.min
        
        trams.sort(key=lambda x: x['data_obj'], reverse=True)
        ultima_tramitacao = trams[0] if trams else None
        
        # Busca informações do órgão atual
        orgao_atual = None
        if 'statusProposicao' in prop and 'siglaOrgao' in prop['statusProposicao']:
            response = requests.get(f"{base_url}/orgaos", params={'sigla': prop['statusProposicao']['siglaOrgao']})
            orgaos = response.json()['dados']
            if orgaos:
                orgao_atual = orgaos[0]
        
        # Gera os links
        id_prop_str = str(id_prop)
        link_pagina = f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={id_prop_str}"
        link_documento = prop.get('urlInteiroTeor', '')
        
        # Formata a resposta
        resposta = f"""
Proposição: {prop['siglaTipo']} {prop['numero']}/{prop['ano']}
Ementa: {prop['ementa']}
        
Situação atual:
- Status: {prop['statusProposicao']['descricaoSituacao']}
- Órgão atual: {prop['statusProposicao']['siglaOrgao']}
{f"  Nome completo: {orgao_atual['nome']}" if orgao_atual else ""}
{f"  Tipo: {orgao_atual['tipoOrgao']}" if orgao_atual else ""}
        
Última tramitação:
- Data: {datetime.strptime(ultima_tramitacao['dataHora'], '%Y-%m-%dT%H:%M').strftime('%d/%m/%Y às %H:%M') if ultima_tramitacao else 'N/A'}
- Órgão: {ultima_tramitacao['siglaOrgao'] if ultima_tramitacao else 'N/A'}
- Despacho: {ultima_tramitacao['despacho'] if ultima_tramitacao else 'N/A'}
- Descrição: {ultima_tramitacao['descricaoTramitacao'] if ultima_tramitacao else 'N/A'}
        
Regime de tramitação: {prop['statusProposicao']['regime']}

Links:
📄 Página da proposição: {link_pagina}
📑 Texto completo: {link_documento}"""

        return resposta
        
    except Exception as e:
        return f"Erro ao consultar proposição: {str(e)}"

if __name__ == "__main__":
    while True:
        print("\nDigite um termo para buscar proposições:")
        print("- Termo de busca: ex: 'fake news'")
        print("- Número: ex: '2306/2020' (busca em todos os tipos)")
        print("- Sigla e número: ex: 'PL 2306/2020', 'PEC 45/2019', 'MPV 1172/2023'")
        print("- Digite 'sair' para encerrar")
        print("\nTipos de proposição:")
        print("PL  - Projeto de Lei")
        print("PLP - Projeto de Lei Complementar")
        print("PEC - Proposta de Emenda à Constituição")
        print("MPV - Medida Provisória")
        print("PDL - Projeto de Decreto Legislativo")
        print("PRC - Projeto de Resolução")
        print("REQ - Requerimento")
        print("INC - Indicação")
        print("RIC - Requerimento de Informação")
        
        termo = input("\nBusca: ")
        if termo.lower() == 'sair':
            break
            
        resultados = buscar_proposicoes(termo)
        
        print(f"\nResultados encontrados: {len(resultados)}")
        for i, res in enumerate(resultados, 1):
            print(f"\n{i}. {res['titulo']}")
            print(f"ID: {res['id']}")
            print(f"Link: {res['link']}")
        
        if resultados:
            escolha = input("\nDigite o número da proposição que deseja consultar (ou Enter para nova busca): ")
            if escolha.isdigit() and 1 <= int(escolha) <= len(resultados):
                id_prop = resultados[int(escolha)-1]['id']
                print("\nConsultando proposição...")
                print(consultar_proposicao_completa(id_prop)) 