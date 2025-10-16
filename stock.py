from database import load_data, save_data

def service_get_all_products():
    """Retorna todos os produtos do 'banco de dados' JSON."""
    data = load_data()
    return data.get("products", [])

def service_get_product(product_id):
    """Busca um produto pelo ID."""
    try:
        product_id = int(product_id)
        data = load_data()
        for product in data.get("products", []):
            if product.get("id") == product_id:
                return product
        return None # Retorna None se não encontrar
    except (ValueError, TypeError):
        return None

def service_create_product(**new_product_data):
    """Cria um novo produto."""
    data = load_data()
    products = data.get("products", [])
    
    # Pega o maior ID atual e adiciona 1 para o novo produto
    new_id = max([p.get("id", 0) for p in products]) + 1 if products else 1
    new_product_data['id'] = new_id
    
    products.append(new_product_data)
    save_data(data)
    
    return True, f"Produto '{new_product_data.get('codigo')}' criado com sucesso!"

def service_remove_product(product_id):
    """Remove um produto pelo ID."""
    try:
        product_id = int(product_id)
        data = load_data()
        products = data.get("products", [])
        
        # Encontra o produto a ser removido
        product_to_remove = None
        for product in products:
            if product.get("id") == product_id:
                product_to_remove = product
                break
        
        if product_to_remove:
            products.remove(product_to_remove)
            save_data(data)
            return True
        return False # Produto não encontrado
    except (ValueError, TypeError):
        return False

# As funções de sugestão e alerta continuam funcionando, mas agora sobre os dados do JSON
def service_generate_acquisition_suggestion():
    """Gera sugestões de compra com base nos dados do JSON."""
    products = service_get_all_products()
    suggestions = []
    for p in products:
        # Lógica simplificada de sugestão (pode ser melhorada)
        necessidade = (p.get('cmm', 0) * 1.5) - p.get('saldo_manut', 0)
        if necessidade > 0:
            suggestions.append({
                "codigo": p.get('codigo'),
                "estoque_atual": p.get('saldo_manut'),
                "cmm": p.get('cmm'),
                "quantidade_a_comprar": round(necessidade)
            })
    return suggestions

def service_check_stock_alerts():
    """Retorna produtos com estoque zerado e CMM maior que 1."""
    products = service_get_all_products()
    alerts = [
        p for p in products 
        if p.get('saldo_manut', 0) == 0 and p.get('cmm', 0) > 1
    ]
    return alerts