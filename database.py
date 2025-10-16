import json
import os

# Caminho para o nosso arquivo de banco de dados JSON
DB_FILE = os.path.join(os.path.dirname(__file__), 'database.json')

def load_data():
    """Carrega todos os dados do arquivo JSON."""
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Se o arquivo não existir, cria uma estrutura vazia
        return {"products": [], "users": [], "sales": []}

def save_data(data):
    """Salva todos os dados de volta no arquivo JSON."""
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)