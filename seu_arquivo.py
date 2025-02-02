import requests
import pandas as pd
from datetime import datetime
import os

class CamaraDownloader:
    def __init__(self):
        self.base_url = "http://dadosabertos.camara.leg.br/arquivos"
    
    def baixar_proposicoes(self, ano, formato='json'):
        """Baixa arquivo de proposições de um determinado ano"""
        url = f"{self.base_url}/proposicoes/{formato}/proposicoes-{ano}.{formato}"
        
        print(f"Baixando proposições de {ano}...")
        try:
            response = requests.get(url)
            if response.status_code == 200:
                filename = f"proposicoes-{ano}.{formato}"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"Arquivo salvo: {filename}")
                return filename
            else:
                print(f"Erro ao baixar arquivo: {response.status_code}")
                return None
        except Exception as e:
            print(f"Erro ao fazer download: {str(e)}")
            return None
    
    def baixar_proposicoes_temas(self, ano, formato='json'):
        """Baixa arquivo de temas das proposições de um determinado ano"""
        url = f"{self.base_url}/proposicoesTemas/{formato}/proposicoesTemas-{ano}.{formato}"
        
        print(f"Baixando temas das proposições de {ano}...")
        try:
            response = requests.get(url)
            if response.status_code == 200:
                filename = f"proposicoesTemas-{ano}.{formato}"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"Arquivo salvo: {filename}")
                return filename
            else:
                print(f"Erro ao baixar arquivo: {response.status_code}")
                return None
        except Exception as e:
            print(f"Erro ao fazer download: {str(e)}")
            return None

def coletar_dados(ano_inicial=2002, ano_final=2024):
    """
    Coleta dados de proposições e seus temas para um período.
    Por padrão coleta de 2002 até o presente, considerando que proposições 
    mais antigas que ~20 anos geralmente não estão mais em tramitação ativa.
    """
    downloader = CamaraDownloader()
    
    # Limpa a pasta dados se ela existir
    if os.path.exists('dados'):
        print("Limpando pasta dados...")
        for arquivo in os.listdir('dados'):
            os.remove(os.path.join('dados', arquivo))
    
    # Cria pasta para armazenar os arquivos se não existir
    os.makedirs('dados', exist_ok=True)
    
    # Para cada ano no intervalo
    for ano in range(ano_inicial, ano_final + 1):
        print(f"\nProcessando ano {ano}...")
        
        # Baixa proposições
        arquivo_prop = downloader.baixar_proposicoes(ano)
        # Baixa temas
        arquivo_temas = downloader.baixar_proposicoes_temas(ano)
        
        if arquivo_prop and arquivo_temas:
            try:
                # Carrega os dados
                proposicoes_json = pd.read_json(arquivo_prop)
                temas_json = pd.read_json(arquivo_temas)
                
                # Converte os dados aninhados em DataFrames
                proposicoes = pd.DataFrame(proposicoes_json['dados'].tolist())
                temas = pd.DataFrame(temas_json['dados'].tolist())
                
                # Tenta fazer o merge usando uri/uriProposicao
                dados_completos = pd.merge(
                    proposicoes,
                    temas,
                    left_on='uri',
                    right_on='uriProposicao',
                    how='left'
                )
                
                # Salva o resultado
                output_file = f'dados/proposicoes_completas_{ano}.csv'
                dados_completos.to_csv(output_file, index=False, encoding='utf-8')
                print(f"Dados completos salvos em: {output_file}")
                
            except Exception as e:
                print(f"Erro ao processar dados do ano {ano}: {str(e)}")
            
            # Remove arquivos temporários
            os.remove(arquivo_prop)
            os.remove(arquivo_temas)
        else:
            print(f"Não foi possível baixar os arquivos para o ano {ano}")

def unificar_dados():
    """Unifica todos os arquivos de proposições completas em um único DataFrame"""
    print("Unificando dados de todos os anos...")
    
    # Lista todos os arquivos de proposições completas
    arquivos = [f for f in os.listdir('dados') if f.startswith('proposicoes_completas_')]
    
    # Cria lista para armazenar os DataFrames
    dfs = []
    
    # Lê cada arquivo e adiciona à lista
    for arquivo in arquivos:
        df = pd.read_csv(os.path.join('dados', arquivo))
        dfs.append(df)
    
    # Concatena todos os DataFrames
    df_completo = pd.concat(dfs, ignore_index=True)
    
    # Salva o resultado
    df_completo.to_csv('dados/proposicoes_completas.csv', index=False, encoding='utf-8')
    print(f"Dados unificados salvos em: dados/proposicoes_completas.csv")
    
    return df_completo

def analisar_dados(df):
    """Realiza análises básicas sobre as proposições"""
    
    print("\nAnálises básicas:")
    
    # Quantidade de proposições por ano
    print("\nQuantidade de proposições por ano:")
    print(df['ano'].value_counts().sort_index())
    
    # Quantidade de proposições por tipo
    print("\nQuantidade de proposições por tipo:")
    print(df['siglaTipo'].value_counts())
    
    # Temas mais comuns
    print("\nTemas mais comuns:")
    print(df['tema'].value_counts().head(10))
    
    # Análise temporal dos temas
    print("\nTemas mais comuns por ano:")
    temas_por_ano = df.groupby(['ano', 'tema']).size().reset_index(name='contagem')
    temas_por_ano = temas_por_ano.sort_values(['ano', 'contagem'], ascending=[True, False])
    
    for ano in temas_por_ano['ano'].unique():
        print(f"\nAno {ano}:")
        print(temas_por_ano[temas_por_ano['ano'] == ano].head(5))

def analisar_tramitacao(df):
    """Analisa detalhes da tramitação das proposições"""
    
    print("\nAnálise da Tramitação:")
    
    try:
        # Converte a string JSON em dicionário
        df['ultimoStatus'] = df['ultimoStatus'].fillna('{}')  # Preenche valores nulos
        df_status = pd.json_normalize(df['ultimoStatus'].apply(eval))
        
        # Adiciona as colunas de status ao DataFrame original
        df_completo = pd.concat([df.reset_index(drop=True), df_status], axis=1)
        
        # Análise por situação atual
        if 'descricaoSituacao' in df_completo.columns:
            print("\nQuantidade de proposições por situação:")
            print(df_completo['descricaoSituacao'].value_counts().head(10))
        else:
            print("\nInformação de situação não disponível")
        
        # Análise por órgão atual
        if 'siglaOrgao' in df_completo.columns:
            print("\nQuantidade de proposições por órgão atual:")
            print(df_completo['siglaOrgao'].value_counts().head(10))
        else:
            print("\nInformação de órgão não disponível")
        
        # Análise de relatoria
        if 'nomeRelator' in df_completo.columns:
            print("\nQuantidade de proposições com relator designado:")
            tem_relator = df_completo['nomeRelator'].notna().sum()
            total = len(df_completo)
            print(f"Com relator: {tem_relator} ({tem_relator/total*100:.2f}%)")
            print(f"Sem relator: {total-tem_relator} ({(total-tem_relator)/total*100:.2f}%)")
        else:
            print("\nInformação de relator não disponível")
        
        # Salva dados de tramitação em arquivo separado
        colunas_tramitacao = [col for col in [
            'id', 'siglaTipo', 'numero', 'ano',  # identificação da proposição
            'dataApresentacao',                   # data inicial
            'descricaoSituacao',                  # situação atual
            'siglaOrgao',                         # órgão atual
            'nomeRelator',                        # relator atual
            'despacho',                           # informação sobre distribuição
            'regime',                             # regime de tramitação
            'descricaoTramitacao',                # última movimentação
            'url'                                 # link para acompanhamento
        ] if col in df_completo.columns]
        
        df_tramitacao = df_completo[colunas_tramitacao].copy()
        df_tramitacao.to_csv('dados/dados_tramitacao.csv', index=False, encoding='utf-8')
        print("\nDados detalhados de tramitação salvos em: dados/dados_tramitacao.csv")
        
        return df_tramitacao
        
    except Exception as e:
        print(f"\nErro na análise de tramitação: {str(e)}")
        return None

def consultar_proposicao(id_ou_sigla):
    """
    Consulta detalhes de uma proposição específica.
    Pode receber tanto o ID quanto a sigla (ex: 'PL 1234/2023')
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
        ultima_tramitacao = trams[0] if trams else None
        
        # Busca informações do órgão atual
        orgao_atual = None
        if 'statusProposicao' in prop and 'siglaOrgao' in prop['statusProposicao']:
            response = requests.get(f"{base_url}/orgaos", params={'sigla': prop['statusProposicao']['siglaOrgao']})
            orgaos = response.json()['dados']
            if orgaos:
                orgao_atual = orgaos[0]
                # Busca membros do órgão (incluindo relator)
                response = requests.get(f"{base_url}/orgaos/{orgao_atual['id']}/membros")
                membros = response.json()['dados']
        
        # Busca o relator atual (se houver)
        relator_info = "Não designado"
        if ultima_tramitacao and 'uriUltimoRelator' in ultima_tramitacao:
            if ultima_tramitacao['uriUltimoRelator']:
                response = requests.get(ultima_tramitacao['uriUltimoRelator'])
                relator_dados = response.json()['dados']
                relator_info = f"""Nome: {relator_dados['nomeCivil']}
Partido: {relator_dados.get('siglaPartido', 'N/A')}
UF: {relator_dados.get('siglaUf', 'N/A')}"""
        
        # Formata a resposta
        resposta = f"""
Proposição: {prop['siglaTipo']} {prop['numero']}/{prop['ano']}
Ementa: {prop['ementa']}
        
Situação atual:
- Status: {prop['statusProposicao']['descricaoSituacao']}
- Órgão atual: {prop['statusProposicao']['siglaOrgao']}
{f"  Nome completo: {orgao_atual['nome']}" if orgao_atual else ""}
{f"  Tipo: {orgao_atual['tipoOrgao']}" if orgao_atual else ""}

Relatoria:
{relator_info}
        
Última tramitação:
- Data: {ultima_tramitacao['dataHora'] if ultima_tramitacao else 'N/A'}
- Despacho: {ultima_tramitacao['despacho'] if ultima_tramitacao else 'N/A'}
- Descrição: {ultima_tramitacao['descricaoTramitacao'] if ultima_tramitacao else 'N/A'}
        
Regime de tramitação: {prop['statusProposicao']['regime']}
Link para acompanhamento: {prop['urlInteiroTeor']}

Histórico recente de tramitação:"""

        # Adiciona as últimas 5 tramitações
        for tram in trams[:5]:
            resposta += f"\n\n{tram['dataHora']}: {tram['descricaoTramitacao']}"
            if tram['despacho']:
                resposta += f"\nDespacho: {tram['despacho']}"

        return resposta
        
    except Exception as e:
        return f"Erro ao consultar proposição: {str(e)}"

if __name__ == "__main__":
    # Coleta dados a partir de 2012
    coletar_dados(2012, 2024)
    
    # Unifica os dados
    df_completo = unificar_dados()
    
    # Realiza análise de tramitação
    df_tramitacao = analisar_tramitacao(df_completo)

    # Pode buscar tanto por ID quanto por sigla
    print(consultar_proposicao("PL 2630/2020"))  # Lei das Fake News
    print(consultar_proposicao(2262847))         # Mesmo projeto, usando ID