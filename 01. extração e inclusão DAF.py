import os
import time
import json
import shutil
import sys
import pandas as pd
import numpy as np
from credenciais import *
from selenium import webdriver
from tkinter import messagebox
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from office365.sharepoint.client_context import ClientContext
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import create_engine

##########funções

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

def aguardar_arquivo(caminho_arquivo, timeout=20):
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

    #Certifique-se de que temos pelo menos dois elementos
    if len(inputs) >= 2:
        #Clicar no primeiro campo de data
        data_inicial_input = inputs[0]
        data_inicial_input.click()
        data_inicial_input.clear()  #Limpa o campo
        data_inicial_input.send_keys(data_inicial)  #Preenche com a data inicial

        #Clicar no segundo campo de data
        data_final_input = inputs[1]
        data_final_input.click()
        data_final_input.clear()  #Limpa o campo
        data_final_input.send_keys(data_final)  #Preenche com a data final

    #Clicar no botão continuar (usando XPath baseado no texto)
    clicar('//*[@id="__next"]/div[3]/div/div/div/div/apw-ng-app/app-template/bb-layout/div[1]/div/div/div/div/bb-layout-column/ng-component/div/div/div/app-demonstrativo-daf-selecao/div/div[2]/div/div/form/bb-card/bb-card-footer/div/button[2]')

    #Clicar no botão download
    clicar('//*[@id="__next"]/div[3]/div/div/div/div/apw-ng-app/app-template/bb-layout/div[1]/div/div/div/div/bb-layout-column/ng-component/div/div/div/app-demonstrativo-daf-final/div/div[2]/div/div/bb-card/bb-card-header/bb-card-header-action/button/bb-icon')
    #Setar a extensão do arquivo
    clicar('//*[contains(text(), "CSV")]')
  
    #Clicar no botão download
    clicar('//*[@id="__next"]/div[3]/div/div/div/div/apw-ng-app/app-template/bb-layout/div[1]/div/div/div/div/bb-layout-column/ng-component/div/div/div/app-demonstrativo-daf-final/div/div[2]/div/div/bb-card/bb-card-header/bb-card-header-action/button/bb-icon')
    #Setar a extensão do arquivo
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

def criar_lancamento(df):
    '''
    cria a observação no site
    '''
    #mapeamento para a tabela 'contabilizacoes' (IDs 1-20)
    dicionario_observacoes = {

        #--- Receitas (tipo_id 1-10) ---
        1: 'REGISTRO DA RECEITA PROVENIENTE DOS ROYALTIES PELA PRODUÇÃO DO PETRÓLEO - ATÉ 5% - LEI 7990/89, REFERENTE A ',
        2: 'REGISTRO DA RECEITA PROVENIENTE DOS ROYALTIES PELA PRODUÇÃO DO PETRÓLEO - EXCEDENTE A 5% - LEI 9478/97, REFERENTE A ',
        3: 'REGISTRO DA RECEITA PROVENIENTE DA PARTICIPAÇÃO ESPECIAL DO PETRÓLEO - PEA, REFERENTE A ',
        4: 'REGISTRO DA RECEITA PROVENIENTE DA COTA PARTE DO FUNDO ESPECIAL DO PETROLEO - FEP, REFERENTE A ',
        5: 'REGISTRO DA RECEITA PROVENIENTE DO FUNDO DE PARTICIPAÇÃO DOS ESTADOS - FPE, REFERENTE A ',
        6: 'REGISTRO DA RECEITA PROVENIENTE DO IMPOSTO SOBRE PRODUTOS INDUSTRIALIZADOS - IPI EXPORTAÇÃO, REFERENTE A ',
        7: 'REGISTRO DA RECEITA PROVENIENTE DA COMPENSAÇÃO FINANCEIRA PELA EXPLORAÇÃO MINERAL - CFM, REFERENTE A ',
        8: 'REGISTRO DA RECEITA PROVENIENTE DA COMPENSAÇÃO FINANCEIRA PELA UTILIZAÇÃO DE RECURSOS HIDRÍCOS - CFH, REFERENTE A ',
        9: 'REGISTRO DA RECEITA PROVENIENTE DA CONTRIBUIÇÃO DE INTERVENÇÃO NO DOMÍNIO ECONÔMICO - CIDE, REFERENTE A ',
        10: 'REGISTRO DA RECEITA PROVENIENTE DA LC 176/2020 (ADO25), REFERENTE A ',

        #--- PASEP (tipo_id 11-20) ---
        11: 'REGISTRO DA TRANSFERÊNCIA DA RETENÇÃO DO PASEP - ROYALTIES PELA PRODUÇÃO DO PETRÓLEO - ATÉ 5% - LEI 7990/89, A ENCARGOS GERAIS, REFERENTE A ',
        12: 'REGISTRO DA TRANSFERÊNCIA DA RETENÇÃO DO PASEP - ROYALTIES PELA PRODUÇÃO DO PETRÓLEO - EXCEDENTE A 5% - LEI 9478/97, A ENCARGOS GERAIS, REFERENTE A ',
        13: 'REGISTRO DA TRANSFERÊNCIA DA RETENÇÃO DO PASEP - PARTICIPAÇÃO ESPECIAL DO PETRÓLEO - PEA, A ENCARGOS GERAIS, REFERENTE A ',
        14: 'REGISTRO DA TRANSFERÊNCIA DA RETENÇÃO DO PASEP - FUNDO ESPECIAL DO PETROLEO - FEP, A ENCARGOS GERAIS, REFERENTE A ',
        15: 'REGISTRO DA TRANSFERÊNCIA DA RETENÇÃO DO PASEP - FUNDO DE PARTICIPAÇÃO DOS ESTADOS - FPE, A ENCARGOS GERAIS, REFERENTE A ',
        16: 'REGISTRO DA TRANSFERÊNCIA DA RETENÇÃO DO PASEP - IMPOSTO SOBRE PRODUTOS INDUSTRIALIZADOS - IPI EXPORTAÇÃO, A ENCARGOS GERAIS, REFERENTE A ',
        17: 'REGISTRO DA TRANSFERÊNCIA DA RETENÇÃO DO PASEP - COMPENSAÇÃO FINANCEIRA PELA EXPLORAÇÃO MINERAL - CFM, A ENCARGOS GERAIS, REFERENTE A ',
        18: 'REGISTRO DA TRANSFERÊNCIA DA RETENÇÃO DO PASEP - COMPENSAÇÃO FINANCEIRA PELA UTILIZAÇÃO DE RECURSOS HIDRÍCOS - CFH, A ENCARGOS GERAIS, REFERENTE A ',
        19: 'REGISTRO DA TRANSFERÊNCIA DA RETENÇÃO DO PASEP - CONTRIBUIÇÃO DE INTERVENÇÃO NO DOMÍNIO ECONÔMICO - CIDE, A ENCARGOS GERAIS, REFERENTE A ',
        20: 'REGISTRO DA TRANSFERÊNCIA DA RETENÇÃO DO PASEP - LC 176/2020 (ADO25), A ENCARGOS GERAIS, REFERENTE A ',
    }

    dicionario_meses = {
        1: 'JANEIRO', 2: 'FEVEREIRO', 3: 'MARÇO', 4: 'ABRIL',
        5: 'MAIO', 6: 'JUNHO', 7: 'JULHO', 8: 'AGOSTO',
        9: 'SETEMBRO', 10: 'OUTUBRO', 11: 'NOVEMBRO', 12: 'DEZEMBRO'
    }

    #criando/formatando colunas 
    df['id'] = None
    df['valor'] = df['valor'].astype(float).round(2)
    df['num_documento'] = None
    df['tempo_contab'] = None
    df['tipo_id'] = None

    #iterando para preencher as colunas
    for index, row in df.iterrows():

        if (row['fundo'] == 'ANP   - ROYALTIES DA ANP'):
       
            if (row['parcela'] == ' ANP-LEI 7990/89'):
                df.loc[index, 'tipo_id'] = 1
                linha_pasep7990 = pd.DataFrame(
                    {'data': [row['data']],
                     'valor': [(np.floor(row['valor']*0.0075*100) / 100)], #cortar as casas decimais e pegar 0,75%
                     'tipo_id': [11]}) 
                df = pd.concat([df, linha_pasep7990], ignore_index=True)
            
            if (row['parcela'] == ' ANP-LEI 9478/97'):
                df.loc[index, 'tipo_id'] = 2
                linha_pasep9478 = pd.DataFrame(
                    {'data': [row['data']],
                     'valor': [(np.floor(row['valor']*0.01*100) / 100)],  #cortar as casas decimais e pegar 1%
                     'tipo_id': [12]})
                df = pd.concat([df, linha_pasep9478], ignore_index=True)

        if (row['fundo'] == 'PEA   - PARTICIPACAO ESPECIAL ANP'):
            if (row['parcela'] == ' PART.ESP.ANP'):
                df.loc[index, 'tipo_id'] = 3
            if (row['parcela'] == ' RETENCAO PASEP'):
                df.loc[index, 'tipo_id'] = 13

        if (row['fundo'] == 'FEP   - FUNDO ESPECIAL DO PETROLEO'):
            if(row['parcela'] == ' COTA-PARTE'):
                df.loc[index, 'tipo_id'] = 4
            if (row['parcela'] == ' RETENCAO PASEP'):
                df.loc[index, 'tipo_id'] = 14

        if (row['fundo'] == 'FPE   - FUNDO DE PARTICIPACAO DOS ESTADOS'):
            if ((row['parcela'] == ' PARCELA DE IPI') | (row['parcela'] == ' PARCELA DE IR')):
                df.loc[index, 'tipo_id'] = 5
            if (row['parcela'] == ' RETENCAO PASEP'):
                df.loc[index, 'tipo_id'] = 15

        if (row['fundo'] == 'IPI   - IPI EXPORTACAO'):
            if ((row['parcela'] == ' IPI - ESTADO') | (row['parcela'] == ' IPI-MUNICIPIOS')):
                df.loc[index, 'tipo_id'] = 6
            if (row['parcela'] == ' PASEP ESTADO'):
                df.loc[index, 'tipo_id'] = 16

        if (row['fundo'] == 'CFM   - COMPENSACAO FINANC. PELA EXPLORACAO MINERAL'):
            if (row['parcela'] == ' CFM-PRD.MINERAL'):
                df.loc[index, 'tipo_id'] = 7
            if (row['parcela'] == ' RETENCAO PASEP'):
                df.loc[index, 'tipo_id'] = 17

        if (row['fundo'] == 'CFH   - COMPENSACAO FINANCEIRA RECURSOS HIDRICOS'):
            if (row['parcela'] == ' CFH-REC.HIDRICO'):
                df.loc[index, 'tipo_id'] = 8
            if (row['parcela'] == ' RETENCAO PASEP'):
                df.loc[index, 'tipo_id'] = 18

        if (row['fundo'] == ''):
            if (row['parcela'] == ''):
                df.loc[index, 'tipo_id'] = 9

        if (row['fundo'] == ''):
            if (row['parcela'] == ''):
                df.loc[index, 'tipo_id'] = 10

    #criando colunas de controle
    df['usuario'] = os.getlogin()
    df['data_hora'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    #criando coluna de observação e filtrando as linhas sem observação
    data_dt = pd.to_datetime(df['data'].astype(str), format='%d/%m/%Y')
    mes = data_dt.dt.month.map(dicionario_meses)
    ano = data_dt.dt.year.astype(str)
    competencia = mes + ' DE ' + ano
    df['observacao'] = df['tipo_id'].map(dicionario_observacoes) + competencia

    #organizando dataframe df_DAF
    df_DAF = df[['fundo', 'data', 'parcela', 'valor', 'tipo']].reset_index(drop=True)
    df_DAF = df_DAF[df_DAF['fundo'].isnull() == False]

    #organizando dataframe df_contab
    df = df[df['observacao'].isnull() == False]
    df.groupby(['fundo', 'data', 'parcela', 'observacao', 'tipo', 'tipo_id'], as_index=False).agg({'valor': 'sum'})
    df_contab = df[['data', 'valor', 'observacao', 'num_documento', 'tipo_id', 'usuario', 'data_hora', 'tempo_contab']].reset_index(drop=True)

    return df_DAF, df_contab

def tratar_dados(caminho_arquivo):
    '''
    trata os dados do csv baixado
    '''
    import sqlite3
    import pandas as pd
    import numpy as np

    df = pd.read_csv(caminho_arquivo, names=['data', 'parcela', 'valor'], header=None)

    #filtrar apenas linhas com dados
    df = df[
        ~(df['data'].isnull() &
        df['parcela'].isnull() &
        df['valor'].isnull())
    ]

    #criar coluna de fundo
    df['fundo'] = np.where(
        df['parcela'] == ' ',
        df['data'],
        np.nan #deixar nulo
    )
    df = df.ffill() #preencher pra baixo

    #filtrar apenas os valores necessários
    df = df[
        (df['data'] != 'DATA/PARCELA/VALOR DISTRIBUIDO') &
        (df['data'] != 'TOTAL POR PARCELA / NATUREZA') &
        (df['data'] != 'TOTAL DISTRIBUIDO NO PERIODO') &
        (df['parcela'] != ' TOTAL NA DATA') &
        (df['valor'] != ' VALOR DISTRIBUIDO') &
        (df['valor'] != ' ')
    ]

    #criar coluna de tipo
    df['tipo'] = df['valor'].str[-1]

    #transformar colunas de valor
    df['valor'] = df['valor'].str.replace('.', '').str.replace('_', '.').str[:-1]

    #transformar coluna de data
    df['data'] = df['data'].str.replace('.', '/')

    #organizar colunas e resetar index
    df = df[['fundo', 'data', 'parcela', 'valor', 'tipo']].reset_index(drop=True)

################################################################################
    #constantes definidas apenas enquanto não é definido um banco de dados
    NOME_TABELA_DAF = 'DAF' #mudar isso aqui futuramente
    NOME_TABELA_CONTAB = 'contabilizacoes'

    #conexão temporária
    con = sqlite3.connect('base_dados.db')
    cursor = con.cursor()
    
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS "{NOME_TABELA_CONTAB}" (
        "id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "data" TEXT NOT NULL,
        "valor" REAL NOT NULL,
        "observacao" TEXT NOT NULL,
        "num_documento" TEXT NULL,
        "tipo_id" INTEGER NOT NULL,
        "usuario" TEXT NOT NULL,
        "data_hora" TEXT NOT NULL,
        "tempo_contab" TEXT NULL
    )
    """)
    con.commit()
    
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS "{NOME_TABELA_DAF}" (
        "id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "fundo" TEXT NOT NULL,
        "data" TEXT NOT NULL,
        "parcela" TEXT NOT NULL,
        "valor" REAL NOT NULL,
        "tipo" TEXT NOT NULL
    )
    """)
    con.commit()
    
################################################################################
    
    #cria df para contabilização
    df_DAF, df_contab = criar_lancamento(df)

    #faz a conferencia para evitar duplicidade de dados no DAF
    df_DAF_conferencia = pd.read_sql(f'''SELECT * FROM {NOME_TABELA_DAF}''', con)
    df_DAF_conferencia = df_DAF.merge(
        df_DAF_conferencia,
        how='left', 
        indicator=True
    )
    df_DAF = df_DAF_conferencia[df_DAF_conferencia['_merge'] == 'left_only']
    df_DAF = df_DAF.drop(columns=['_merge'])
    
    if not df_DAF.empty:
        df_DAF.to_sql(NOME_TABELA_DAF, con, if_exists='append', index=False)
        print("Info", "Documento DAF carregado com sucesso!")
    else:
        print("Info", "Nenhum novo documento para processar!")
    
    #faz a conferencia para evitar duplicidade de dados na contabilização
    df_contab_conferencia = pd.read_sql(f'''SELECT * FROM {NOME_TABELA_CONTAB}''', con)
    df_contab_conferencia = df_contab.merge(
        df_contab_conferencia,
        on=['data', 'valor', 'observacao', 'tipo_id'],
        how='left', 
        indicator=True
    )
    df_contab = df_contab_conferencia[df_contab_conferencia['_merge'] == 'left_only']
    df_contab = df_contab.drop(columns=['_merge', 'num_documento_y', 'usuario_y', 'data_hora_y', 'tempo_contab_y'])
    df_contab = df_contab.rename(columns={'num_documento_x': 'num_documento', 'usuario_x': 'usuario', 'data_hora_x': 'data_hora', 'tempo_contab_x': 'tempo_contab'})

    if not df_contab.empty:
        df_contab.to_sql(NOME_TABELA_CONTAB, con, if_exists='append', index=False)
        print("Info", "Documento contabilização carregado com sucesso!")
    else:
        print("Info", "Nenhum novo documento para processar!")
        
    con.close()

def excluir_arquivo(caminho_arquivo):
    if os.path.exists(caminho_arquivo):
        os.remove(caminho_arquivo)

def coletar_cookies():

    from playwright.sync_api import sync_playwright
 
    site_url = url_sharepoint
    storage_state_path = "./storage_state.json"

    try:
    
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='msedge', headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto(site_url)
            
            #esperar pela conexão entrar em idle
            page.wait_for_load_state("networkidle")

            print("\nFaça o login no SharePoint e aguarde...")
            input("Quando a página estiver completamente carregada e autorizada, aperte Enter no terminal para continuar...")

            #guardar os cookies
            context.storage_state(path=storage_state_path)
            print(f"Saved Playwright storage state to: {storage_state_path}")

            context.close()
            browser.close()
            
            global ctx, web

            ctx = ClientContext(url_sharepoint).with_cookies(autenticar)
            web = ctx.web.get().execute_query()
    
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu algum erro ao se conectar ao Sharepoint: {e}")
        sys.exit()


##########parâmetros

#define o caminho do arquivo baixado
caminho_arquivo_csv = fr'C:\Users\{os.getlogin()}\Downloads\demonstrativoDAF.csv'
caminho_arquivo_pdf = fr'C:\Users\{os.getlogin()}\Downloads\demonstrativo-daf.pdf'

try:
    #conecta-se ao sharepoint
    ctx = ClientContext(url_sharepoint).with_cookies(autenticar)
    web = ctx.web.get().execute_query()

except Exception as e:
    coletar_cookies()

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


##########execução


try:
    #limpa os arquivos antigos, caso existam
    excluir_arquivo(caminho_arquivo_csv)
    excluir_arquivo(caminho_arquivo_pdf)

    #baixa e ronomeia o DAF do mês atual, em CVS e PDF
    baixar_daf(f'01/{mes:02d}/{ano}', f'{dia:02d}/{mes:02d}/{ano}')


    #para csv
    aguardar_arquivo(caminho_arquivo_csv)
    novo_caminho_arquivo_csv = renomear_arquivo(caminho_arquivo_csv, f"DAF - {ano}.{mes:02d}.csv")
    tratar_dados(novo_caminho_arquivo_csv) #para csv, coloca-se os dados no banco
    upload(caminho_pasta_csv_sharepoint, novo_caminho_arquivo_csv)

    #para pdf
    aguardar_arquivo(caminho_arquivo_pdf)
    novo_caminho_arquivo_pdf = renomear_arquivo(caminho_arquivo_pdf, f"DAF - {ano}.{mes:02d}.pdf")
    upload(caminho_pasta_pdf_sharepoint, novo_caminho_arquivo_pdf)

except Exception as e:
    driver.quit()
    messagebox.showerror("Error", f"Ocorreu algum erro ao baixar o DAF do mês corrente: {e}")
    sys.exit()

#verifica se o dia atual é menor ou igual a 3
if dia <= 3:

    try:

        #define as datas a serem usadas caso o dia atual seja menor ou igual a 3
        ultimo_dia = datetime.now().replace(day=1) - timedelta(days=1)
        dia = ultimo_dia.day
        mes = datetime.now().month - 1

        #excluir arquivos antigos; CSV
        excluir_arquivo(caminho_arquivo_csv)
        excluir_arquivo(caminho_arquivo_pdf)

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
    
    except Exception as e:
        driver.quit()
        messagebox.showerror("Error", f"Ocorreu algum erro ao baixar o DAF do mês anterior: {e}")
        sys.exit()

#finaliza o navegador
driver.quit()