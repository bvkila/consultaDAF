import os
import time
import shutil
import calendar
from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import date, timedelta
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# -----------------------------------------------

user = os.getlogin()
caminho_arquivo = fr'C:\Users\{user}\Downloads\demonstrativoDAF.csv'

service = Service()
edge_options = Options()
edge_options.add_argument("--start-maximized")
# edge_options.add_argument("--headless") # Para rodar em segundo plano
edge_options.add_argument("--log-level=3")
driver = webdriver.Edge(service=service, options=edge_options)
driver.maximize_window()

def clicar(xpath):
    elemento = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    elemento.click()

def digitar(xpath, texto):
    elemento = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    elemento.clear()
    elemento.send_keys(texto)

def gerar_intervalos_mensais_padrao(data_inicio_str, data_fim_str):
    """
    Gera tuplas com a data inicial e final de cada mês dentro de um intervalo.
    Usa as bibliotecas padrão do Python.

    Args:
        data_inicio_str (str): A data de início no formato 'YYYY-MM-DD'.
        data_fim_str (str): A data de fim no formato 'YYYY-MM-DD'.

    Yields:
        tuple: Uma tupla contendo (primeiro_dia_do_mes, ultimo_dia_do_mes).
    """

    data_inicio = date.fromisoformat(data_inicio_str)
    data_fim = date.fromisoformat(data_fim_str)

    # Começamos pelo primeiro dia do mês da data de início
    current_date = data_inicio.replace(day=1)

    while current_date <= data_fim:
        # Encontra o último dia do mês corrente
        _, num_dias_no_mes = calendar.monthrange(current_date.year, current_date.month)
        data_fim_mes = current_date.replace(day=num_dias_no_mes)

        # A data inicial do nosso intervalo é a própria current_date
        data_inicio_mes = current_date
        
        # Garante que não ultrapassemos a data final geral
        # Isso é importante para o último mês do intervalo
        if data_fim_mes > data_fim:
            data_fim_mes = data_fim
            
        yield (data_inicio_mes, data_fim_mes)

        # Move para o primeiro dia do próximo mês
        current_date = (data_fim_mes + timedelta(days=1))

# -----------------------------------------------

data_inicial_range = '2009-12-01'
data_final_range = '2025-08-31'

for inicio, fim in gerar_intervalos_mensais_padrao(data_inicial_range, data_final_range):
    
    data_inicial = f'{inicio.day:02d}/{inicio.month:02d}/{inicio.year}'
    data_final = f'{fim.day:02d}/{fim.month:02d}/{fim.year}'
    
    # O .strftime() é só para formatar a data para impressão
    print(f"Mês: {inicio.strftime('%Y-%m')}, Início: {inicio.strftime('%Y-%m-%d')}, Fim: {fim.strftime('%Y-%m-%d')}")

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

        # Clicar em um lugar fora do campo para "fechar" o elemento
        body = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="angular-component-container"]/apw-ng-app/app-template/bb-layout/div[1]/div/div/div/div/bb-layout-column/ng-component/div/div/div/app-demonstrativo-daf-selecao/div/div[1]/div/div/h4')))
        body.click()

        # Clicar no segundo campo de data
        data_final_input = inputs[1]
        data_final_input.click()
        data_final_input.clear()  # Limpa o campo
        data_final_input.send_keys(data_final)  # Preenche com a data final

        body.click()


    # Clicar no botão continuar (usando XPath baseado no texto)
    clicar('//*[@id="__next"]/div[3]/div/div/div/div/apw-ng-app/app-template/bb-layout/div[1]/div/div/div/div/bb-layout-column/ng-component/div/div/div/app-demonstrativo-daf-selecao/div/div[2]/div/div/form/bb-card/bb-card-footer/div/button[2]')

    # Clicar no botão download
    clicar('//*[@id="__next"]/div[3]/div/div/div/div/apw-ng-app/app-template/bb-layout/div[1]/div/div/div/div/bb-layout-column/ng-component/div/div/div/app-demonstrativo-daf-final/div/div[2]/div/div/bb-card/bb-card-header/bb-card-header-action/button/bb-icon')

    # Setar a extensão do arquivo
    clicar('//*[contains(text(), "CSV")]')

    # Aguardar a conclusão do download e garantir que o arquivo seja renomeado no momento do download
    time.sleep(1)

    diretorio = os.path.dirname(caminho_arquivo)
    novo_nome = f"DAF - {inicio.year:02d}.{inicio.month:02d}.csv"
    novo_caminho = os.path.join(diretorio, novo_nome)
    shutil.move(caminho_arquivo, novo_caminho)