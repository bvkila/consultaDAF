import os
import time
import shutil
import json
from credenciais import *
from office365.sharepoint.client_context import ClientContext
from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

########## funções

def clicar(xpath):
    '''
    clica em um elemento identificado pelo xpath
    '''
    elemento = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    elemento.click()

def digitar(xpath, texto):
    '''
    digita um texto em um elemento identificado pelo xpath
    '''
    elemento = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    elemento.clear()
    elemento.send_keys(texto)

def aguardar_arquivo(caminho_arquivo, timeout=10):
    '''
    aguarda até que um arquivo exista no caminho especificado ou até que o tempo limite seja atingido
    '''
    inicio = time.time()
    while not os.path.exists(caminho_arquivo):
        if time.time() - inicio > timeout:
            raise TimeoutError(f"O arquivo {caminho_arquivo} não foi encontrado dentro do tempo limite de {timeout} segundos.")
        time.sleep(1)

def renomear_arquivo(caminho_antigo, novo_nome):
    '''
    renomeia um arquivo, usando como argumentos o nome atual e o novo nome do arquivo
    '''
    diretorio = os.path.dirname(caminho_antigo)
    novo_caminho = os.path.join(diretorio, novo_nome)
    shutil.move(caminho_antigo, novo_caminho)

    return novo_caminho

def baixar_daf(data_inicial, data_final):
    '''
    baixa o demonstrativo de arrecadação federal baseado nas datas inicial e final
    '''
    #abrir navegador
    driver.get('https://demonstrativos.apps.bb.com.br/arrecadacao-federal')

    #preencher nome do Estado
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.ng-pristine[formcontrolname='nomeBeneficiarioEntrada']"))).send_keys('RIO DE JANEIRO')
    clicar('//*[@id="angular-component-container"]/apw-ng-app/app-template/bb-layout/div/div/div/div/div/bb-layout-column/ng-component/div/div/div/app-demonstrativo-daf/form/div/div/div/bb-card/bb-card-footer/div[2]/button')

    inputs = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[placeholder='DD / MM / AAAA']")))

    # Certifique-se de que temos pelo menos dois elementos
    if len(inputs) >= 2:
        # Clicar no primeiro campo de data
        data_inicial_input = inputs[0]
        data_inicial_input.click()
        data_inicial_input.clear()  # Limpa o campo
        data_inicial_input.send_keys(data_inicial)  # Preenche com a data inicial

        # Clicar no segundo campo de data
        data_final_input = inputs[1]
        data_final_input.click()
        data_final_input.clear()  # Limpa o campo
        data_final_input.send_keys(data_final)  # Preenche com a data final

    # Clicar no botão continuar (usando XPath baseado no texto)
    clicar('//*[@id="__next"]/div[3]/div/div/div/div/apw-ng-app/app-template/bb-layout/div[1]/div/div/div/div/bb-layout-column/ng-component/div/div/div/app-demonstrativo-daf-selecao/div/div[2]/div/div/form/bb-card/bb-card-footer/div/button[2]')

    # Clicar no botão download
    clicar('//*[@id="__next"]/div[3]/div/div/div/div/apw-ng-app/app-template/bb-layout/div[1]/div/div/div/div/bb-layout-column/ng-component/div/div/div/app-demonstrativo-daf-final/div/div[2]/div/div/bb-card/bb-card-header/bb-card-header-action/button/bb-icon')
    # Setar a extensão do arquivo
    clicar('//*[contains(text(), "CSV")]')
  
    # Clicar no botão download
    clicar('//*[@id="__next"]/div[3]/div/div/div/div/apw-ng-app/app-template/bb-layout/div[1]/div/div/div/div/bb-layout-column/ng-component/div/div/div/app-demonstrativo-daf-final/div/div[2]/div/div/bb-card/bb-card-header/bb-card-header-action/button/bb-icon')
    # Setar a extensão do arquivo
    clicar('//*[contains(text(), "PDF")]')

def autenticar():
    '''
    abre o json carregado com os cookies e seleciona os cookies necessarios
    '''
    with open("./storage_state.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    cookies = {}
    
    for c in data.get("cookies", []):
        name = c.get("name")
        if name in {"FedAuth", "rtFa", "SPOIDCRL"}:
            cookies[name] = c.get("value", "")
    
    return cookies

def upload(pasta_sharepoint, caminho_local):
    '''
    faz o upload do arquivo no caminho_local para a pasta_sharepoint
    '''
    file_name = os.path.basename(caminho_local)
    
    try:
        
        target_folder = ctx.web.get_folder_by_server_relative_url(pasta_sharepoint)
        
        with open(caminho_local, "rb") as f:
            target_folder.files.upload(f, file_name).execute_query()
        print(f"Documento '{file_name}' foi carregado com sucesso!")
   
    except Exception as e:
        print(f"Error uploading file: {e}")

def tratar_dados(caminho_arquivo):
    '''
    trata os dados do csv baixado
    '''
    import sqlite3
    import pandas as pd
    import numpy as np

    df = pd.read_csv(caminho_arquivo, names=['data', 'parcela', 'valor'], header=None)

    # filtrar apenas linhas com dados
    df = df[
        ~(df['data'].isnull() &
        df['parcela'].isnull() &
        df['valor'].isnull())
    ]

    # criar coluna de fundo
    df['fundo'] = np.where(
        df['parcela'] == ' ',
        df['data'],
        np.nan # deixar nulo
    )
    df = df.fillna(method='ffill') # preencher pra baixo

    # filtrar apenas os valores necessários
    df = df[
        (df['data'] != 'DATA/PARCELA/VALOR DISTRIBUIDO') &
        (df['data'] != 'TOTAL POR PARCELA / NATUREZA') &
        (df['data'] != 'TOTAL DISTRIBUIDO NO PERIODO') &
        (df['parcela'] != ' TOTAL NA DATA') &
        (df['valor'] != ' VALOR DISTRIBUIDO') &
        (df['valor'] != ' ')
    ]

    # criar coluna de tipo
    df['tipo'] = df['valor'].str[-1]

    # transformar colunas de valor
    df['valor'] = df['valor'].str.replace('.', '').str.replace('_', '.').str[:-1]

    # transformar coluna de data
    df['data'] = df['data'].str.replace('.', '/')

    # organizar colunas e resetar index
    df = df[['fundo', 'data', 'parcela', 'valor', 'tipo']].reset_index(drop=True)

    # constantes definidas apenas enquanto não é definido um banco de dados
    NOME_TABELA = 'base_dados' # mudar isso aqui futuramente

    #conexão temporária
    con = sqlite3.connect('base_dados.db')
    cursor = con.cursor()

    # transforma a consulta em um dataframe
    base = pd.read_sql_query(f'''
    SELECT * FROM {NOME_TABELA}
    ''', con)

    #verifica se cada row já está no banco de dados
    for index, row in df.iterrows():

        #cria uma conferência de duplicidade
        conferencia_duplicidade = base[(base['fundo'] == row['fundo'])&
                                (base['data'] == row['data'])&
                                (base['parcela'] == row['parcela'])&
                                (base['valor'] == row['valor'])&
                                (base['tipo'] == row['tipo'])]

        #se já existir, nao inserir novamente
        if not conferencia_duplicidade.empty:
            continue

        #se não existir, inserir no banco de dado
        else:

            cursor.execute(f'''
            INSERT INTO {NOME_TABELA} (fundo, data, parcela, valor, tipo)
            VALUES (?, ?, ?, ?, ?)
            ''', [row['fundo'], row['data'], row['parcela'], row['valor'], row['tipo']])
            con.commit()  # precisa dar o commit para salvar as alterações
                    
    con.close()
    print("Info", "Documentos processados com sucesso!")

########## parâmetros

#define o caminho do arquivo baixado
caminho_arquivo_csv = fr'C:\Users\{os.getlogin()}\Downloads\demonstrativoDAF.csv'
caminho_arquivo_pdf = fr'C:\Users\{os.getlogin()}\Downloads\demonstrativo-daf.pdf'

#configurações iniciais do Edge
service = Service()
edge_options = Options()
edge_options.add_argument("--start-maximized")
edge_options.add_argument("--headless")
edge_options.add_argument("--log-level=3")
driver = webdriver.Edge(service=service, options=edge_options)
driver.maximize_window()

#define as datas a serem usadas
ano = datetime.now().year
dia = datetime.now().day
mes = datetime.now().month


########## execução

#excluir arquivos antigos; CSV
try:
    os.remove(caminho_arquivo_csv)
except:
    pass

#excluir arquivos antigos; PDF
try:
    os.remove(caminho_arquivo_pdf)
except:
    pass

#baixa e ronomeia o DAF do mês atual
baixar_daf(f'01/{mes:02d}/{ano}', f'{dia:02d}/{mes:02d}/{ano}')

#conecta-se ao sharepoint
ctx = ClientContext(url_sharepoint).with_cookies(autenticar)
web = ctx.web.get().execute_query()

#para csv
aguardar_arquivo(caminho_arquivo_csv)
novo_caminho_arquivo_csv = renomear_arquivo(caminho_arquivo_csv, f"DAF - {ano}.{mes:02d}.csv")
tratar_dados(novo_caminho_arquivo_csv)
upload(caminho_pasta_csv_sharepoint, novo_caminho_arquivo_csv)

#para pdf
aguardar_arquivo(caminho_arquivo_pdf)
novo_caminho_arquivo_pdf = renomear_arquivo(caminho_arquivo_pdf, f"DAF - {ano}.{mes:02d}.pdf")
upload(caminho_pasta_pdf_sharepoint, novo_caminho_arquivo_pdf)

#verifica se o dia atual é menor ou igual a 3
if dia <= 3:
    #define as datas a serem usadas caso o dia atual seja menor ou igual a 3
    ultimo_dia = datetime.now().replace(day=1) - timedelta(days=1)
    dia = ultimo_dia.day
    mes = datetime.now().month - 1

    #excluir arquivos antigos; CSV
    try:
        os.remove(caminho_arquivo_csv)
    except:
        pass

    #excluir arquivos antigos; PDF
    try:
        os.remove(caminho_arquivo_pdf)
    except:
        pass

    #baixa e ronomeia o DAF do mês anterior
    baixar_daf(f'01/{mes:02d}/{ano}', f'{dia:02d}/{mes:02d}/{ano}')
    
    #para csv
    aguardar_arquivo(caminho_arquivo_csv)
    novo_caminho_arquivo_csv = renomear_arquivo(caminho_arquivo_csv, f"DAF - {ano}.{mes:02d}.csv")
    tratar_dados(novo_caminho_arquivo_csv)
    upload(caminho_pasta_csv_sharepoint, novo_caminho_arquivo_csv)
    
    #para pdf
    aguardar_arquivo(caminho_arquivo_pdf)
    novo_caminho_arquivo_pdf = renomear_arquivo(caminho_arquivo_pdf, f"DAF - {ano}.{mes:02d}.pdf")
    upload(caminho_pasta_pdf_sharepoint, novo_caminho_arquivo_pdf)

#finaliza o navegador
driver.quit()