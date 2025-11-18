import pandas as pd
import numpy as np
import sqlite3
import glob


caminho = r'C:\Users\jbraga\Downloads\extratos\*.csv'
arquivos = glob.glob(caminho)

for caminho_arquivo in arquivos:
        
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
    df['valor'] = df['valor'].astype(float)

    # transformar coluna de data
    df['data'] = df['data'].str.replace('.', '/')

    # organizar colunas e resetar index
    df = df[['fundo', 'data', 'parcela', 'valor', 'tipo']].reset_index(drop=True)

    # constantes definidas apenas enquanto não é definido um banco de dados
    NOME_TABELA = 'teste_DAF' # mudar isso aqui futuramente

    #conexão temporária
    con = sqlite3.connect('base_dados.db')
    cursor = con.cursor()

    # df.to_sql(NOME_TABELA, con, if_exists='replace', index=False)

    # transforma a consulta em um dataframe
    base = pd.read_sql_query(f'''
    SELECT * FROM {NOME_TABELA}
    ''', con)

    #verifica se cada row já está no banco de dados
    for index, row in df.iterrows():

        #cria uma conferência de duplicidade
        conferencia_duplicidade = base[
            (base['fundo'] == row['fundo'])&
            (base['data'] == row['data'])&
            (base['parcela'] == row['parcela'])&
            (base['valor'] == row['valor'])&
            (base['tipo'] == row['tipo'])
        ]

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