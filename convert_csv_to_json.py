import pandas as pd
import json

# Carrega os dados do CSV
try:
    df_products = pd.read_csv('dados_hackathon.csv', delimiter=';')
    print(f"{len(df_products)} produtos carregados do CSV.")
except FileNotFoundError:
    print("Erro: Arquivo 'dados_hackathon.csv' não encontrado.")
    exit()

# Adiciona um ID único para cada produto, já que não temos um no CSV
df_products.reset_index(inplace=True)
df_products.rename(columns={'index': 'id'}, inplace=True)
# Começa o ID do 1 em vez do 0
df_products['id'] = df_products['id'] + 1

# Converte o DataFrame para uma lista de dicionários
products_list = df_products.to_dict(orient='records')

# Estrutura inicial do nosso "banco de dados"
db_data = {
    "products": products_list,
    "users": [], # Adicionamos uma lista vazia para usuários
    "sales": []    # E uma lista vazia para vendas
}

# Salva tudo no arquivo JSON
with open('database.json', 'w', encoding='utf-8') as f:
    json.dump(db_data, f, ensure_ascii=False, indent=4)

print("✅ Arquivo 'database.json' criado com sucesso!")