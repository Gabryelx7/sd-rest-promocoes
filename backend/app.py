from flask import Flask, jsonify, request
from backend.gateway import (
    list_promotions,
    register_promotion,
    vote_on_promotion
)

app = Flask(__name__)

interests = []

# Lista promoções
@app.route('/promotions', methods=['GET'])
def get_promotions():
    published_promos = list_promotions()
    return jsonify(published_promos), 200

# Cadastra uma nova promoção
@app.route('/promotions', methods=['POST'])
def post_promotion():
    request_body = request.get_json()
    new_promo = register_promotion(request_body)
    if new_promo:
        return jsonify(new_promo), 201
    
    return jsonify(new_promo), 400

# Vota em uma promoção
@app.route('/promotions/<int:promo_id>', methods=['POST'])
def vote_on_promotion(promo_id):
    updated_data = request.get_json()
    vote_response = vote_on_promotion(promo_id, updated_data)
    if vote_response:
        return jsonify(vote_response), 201
    
    return jsonify({"error": "Item not found"}), 404

# Registra interesse em uma categoria
@app.route('/interests', methods=['POST'])
def post_interest():
    new_interest = request.get_json()
    if "interest" in new_interest:
        new_interest["id"] = len(interests) + 1
        interests.append(new_interest)
        return jsonify(new_interest), 201

    return jsonify({"error": "Bad Request"}), 400

# Remove interesse em uma categoria
@app.route('/interests/<int:interest_id>', methods=['DELETE'])
def delete_interest(interest_id):
    global interests
    interest = next((interest for interest in interests if interest["id"] == interest_id), None)
    if interest:
        interests = [interest for interest in interests if interest["id"] != interest_id]
        return jsonify({"message": "Interest deleted"}), 200
    else:
        return jsonify({"error": "Item not found"}), 404
    
if __name__ == '__main__':
    app.run(debug=True)
