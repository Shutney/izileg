import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def buscar_proposicoes(termo):
    """
    Busca proposições usando o termo de busca ou número
    Aceita formatos:
    - Termo de busca: "fake news"
    - Número: "2306/2020"
    - Sigla e número: "PL 2306/2020", "PEC 45/2019", etc
    """
    # Lista de tipos comuns de proposições
    TIPOS_PROPOSICOES = [
        'PL',    # Projeto de Lei
        'PLP',   # Projeto de Lei Complementar
        'PEC',   # Proposta de Emenda à Constituição
        'MPV',   # Medida Provisória
        'PDL',   # Projeto de Decreto Legislativo
        'PRC',   # Projeto de Resolução
        'REQ',   # Requerimento
        'INC',   # Indicação
        'RIC',   # Requerimento de Informação
        'PDC',   # Projeto de Decreto Legislativo
    ]
    
    # Verifica se é uma busca por número
    if '/' in termo:
        resultados = []
        numero_ano = termo
        
        # Se tem sigla específica
        if ' ' in termo:
            sigla, numero_ano = termo.split(' ')
            tipos_busca = [sigla.upper()]
        else:
            # Se não tem sigla, busca em todos os tipos
            tipos_busca = TIPOS_PROPOSICOES
        
        numero, ano = numero_ano.split('/')
        
        # Busca em cada tipo de proposição
        for tipo in tipos_busca:
            try:
                url = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"
                params = {
                    'siglaTipo': tipo,
                    'numero': numero,
                    'ano': ano
                }
                response = requests.get(url, params=params)
                dados = response.json()['dados']
                
                for prop in dados:
                    resultados.append({
                        'titulo': f"{prop['siglaTipo']} {prop['numero']}/{prop['ano']} - {prop['ementa'][:100]}...",
                        'id': prop['id'],
                        'link': f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={prop['id']}"
                    })
            except Exception as e:
                print(f"Erro ao buscar {tipo}: {str(e)}")
                continue
        
        if resultados:
            return resultados
        else:
            # Adiciona mensagem sugerindo especificar o tipo
            tipos_exemplo = ", ".join(TIPOS_PROPOSICOES[:3])  # Mostra só os 3 primeiros como exemplo
            return [{'titulo': f"Nenhuma proposição encontrada com número {numero}/{ano}. \n\nTente especificar o tipo, por exemplo:\n- {tipos_exemplo} {numero}/{ano}",
                    'id': None,
                    'link': None}]
    
    # Busca normal por termo
    url = "https://www.camara.leg.br/busca-portal/proposicoes"
    params = {
        'pagina': 1,
        'ordem': 'relevancia',
        'q': termo
    }
    
    try:
        response = requests.get(url, params=params)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        resultados = []
        items = soup.find_all('div', class_='resultItemContent')
        
        for item in items:
            titulo = item.find('a', class_='nomeProposicao')
            if titulo:
                link = titulo.get('href', '')
                id_prop = re.search(r'idProposicao=(\d+)', link)
                if id_prop:
                    resultados.append({
                        'titulo': titulo.text.strip(),
                        'id': id_prop.group(1),
                        'link': f"https://www.camara.leg.br{link}"
                    })
        
        return resultados
    
    except Exception as e:
        print(f"Erro na busca: {str(e)}")
        return []

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

def consultar_proposicao_completa(id_ou_sigla):
    """
    Consulta informações tanto da API quanto da página web
    """
    # Primeiro consulta a API
    resultado_api = consultar_proposicao(id_ou_sigla)
    
    # Se for uma sigla, precisa obter o ID
    if isinstance(id_ou_sigla, str):
        sigla_tipo, numero_ano = id_ou_sigla.split(' ')
        numero, ano = numero_ano.split('/')
        response = requests.get(
            "https://dadosabertos.camara.leg.br/api/v2/proposicoes",
            params={'siglaTipo': sigla_tipo, 'numero': numero, 'ano': ano}
        )
        dados = response.json()['dados']
        if dados:
            id_prop = dados[0]['id']
            # Consulta a página web
            resultado_web = consultar_tramitacao_web(id_prop)
            return f"{resultado_api}\n\n{resultado_web}"
    
    return resultado_api

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