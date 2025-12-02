import pandas as pd
import numpy as np
import glob

caminho = r'C:\Users\jbraga\Downloads\extratos\*.csv'
arquivos = glob.glob(caminho)

def criar_lancamento(df):
    '''
    cria a observação no site
    '''

    import os
    from datetime import datetime
    
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

for caminho_arquivo in arquivos:
    print(f"Processando {caminho_arquivo}!")
    tratar_dados(caminho_arquivo)