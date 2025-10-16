from flask import Flask, request, jsonify
from flask_cors import CORS
import stock
# sales e worker seriam importados aqui também se fossem refatorados

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "Nexum API (JSON version) is running!"}), 200

# --- Rotas de Produtos ---

@app.route('/api/products', methods=['GET'])
def get_all_products():
    """Endpoint para listar todos os produtos."""
    products = stock.service_get_all_products()
    return jsonify(products)

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Endpoint para buscar um produto específico pelo ID."""
    product = stock.service_get_product(product_id)
    if product:
        return jsonify(product)
    return jsonify({"error": "Product not found"}), 404

@app.route('/api/products', methods=['POST'])
def create_product():
    """Endpoint para criar um novo produto."""
    data = request.json
    success, message = stock.service_create_product(**data)
    if success:
        return jsonify({"message": message}), 201
    return jsonify({"error": message}), 400

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Endpoint para remover um produto."""
    if stock.service_remove_product(product_id):
        return jsonify({"message": "Product removed successfully"}), 200
    return jsonify({"error": "Product not found or could not be removed"}), 404

@app.route('/api/suggestions/acquisition', methods=['GET'])
def get_acquisition_suggestions():
    """Endpoint que retorna sugestões de compra."""
    suggestions = stock.service_generate_acquisition_suggestion()
    return jsonify(suggestions)

@app.route('/api/alerts/stock', methods=['GET'])
def get_stock_alerts():
    """Endpoint que retorna produtos críticos."""
    alerts = stock.service_check_stock_alerts()
    return jsonify(alerts)

# --- Execução da Aplicação ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)