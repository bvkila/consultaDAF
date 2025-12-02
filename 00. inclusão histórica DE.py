import pandas as pd
import sqlite3

caminho_arquivo = r"C:\Users\jbraga\Downloads\B - Dados Externos ao DAF.xlsx"
df = pd.read_excel(caminho_arquivo, sheet_name="externos")

#conexão temporária
con = sqlite3.connect('base_dados.db')

print(df)
df.to_sql('externos', con, if_exists='replace')