from datetime import datetime
from database import fetch_all, fetch_one, execute_query

def validate_date_format(date_str):
    try:
        datetime.strptime(date_str, "%d/%m/%Y")
        return True
    except ValueError:
        return False

def service_get_all_sales():
    return fetch_all("SELECT * FROM supply_chain.vendas")

def service_get_sale(sale_id):
    return fetch_one("SELECT * FROM supply_chain.vendas WHERE id = ?", (sale_id,))

def service_create_sale(name, sale_value, sale_date):
    if not sale_date or not validate_date_format(sale_date):
        return None, "Data inválida! Formato DD/MM/AAAA."
    
    query = 'INSERT INTO supply_chain.vendas (nome_venda, valor_venda, data_venda) VALUES (?, ?, ?)'
    
    success, result_or_error = execute_query(
        query,
        (name, sale_value, sale_date)
    )
    
    if success:
        return 'ID_INSERIDO', "Venda registrada com sucesso!"
    else:
        return None, f"Falha ao registrar venda: {result_or_error}"

def service_update_sale(sale_id, name, sale_value, sale_date):
    current_sale = service_get_sale(sale_id)
    if not current_sale: return False, "Venda não encontrada!"
    if sale_date and not validate_date_format(sale_date): return False, "Data de venda inválida! Formato DD/MM/AAAA."
        
    new_name = name if name is not None else current_sale.get('nome_venda')
    new_value = sale_value if sale_value is not None else current_sale.get('valor_venda')
    new_date = sale_date if sale_date is not None else current_sale.get('data_venda')
    
    query = 'UPDATE supply_chain.vendas SET nome_venda = ?, valor_venda = ?, data_venda = ? WHERE id = ?'
    
    success, updated_count = execute_query(
        query,
        (new_name, new_value, new_date, sale_id)
    )
    
    return success and updated_count > 0, "Venda atualizada com sucesso!" if success and updated_count > 0 else "Venda não encontrada ou falha na atualização."

def service_remove_sale(sale_id):
    query = 'DELETE FROM supply_chain.vendas WHERE id = ?'
    success, deleted_count = execute_query(query, (sale_id,))
    return success and deleted_count > 0