import sqlite3
import pandas as pd
import numpy as np

df = pd.read_csv('DAF - 2025.11.csv', names=['data', 'parcela', 'valor'], header=None)

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

print(df)

con = sqlite3.connect('base_dados.db')
cursor = con.cursor()

query = """
    INSERT OR IGNORE INTO base_dados (fundo, data, parcela, valor, tipo) 
    VALUES (?, ?, ?, ?, ?);
"""

for index, row in df.iterrows():
    print(row['fundo'], row['data'], row['parcela'], row['valor'], row['tipo'])
    cursor.execute(query, (row['fundo'], row['data'], row['parcela'], row['valor'], row['tipo']))
