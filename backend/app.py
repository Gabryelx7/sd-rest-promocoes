import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_sse import sse
from backend.gateway import (
    list_promotions,
    register_promotion,
    vote_on_promotion,
    register_interest,
    remove_interest
)

app = Flask(__name__)

load_dotenv()

app.config["REDIS_URL"] = os.getenv("REDIS_URL")
app.register_blueprint(sse, url_prefix='/stream')

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
@app.route('/promotions/<string:promo_id>', methods=['POST'])
def vote_promotion_route(promo_id):
    updated_data = request.get_json()
    vote_response = vote_on_promotion(promo_id, updated_data)
    if vote_response:
        return jsonify(vote_response), 201
    
    return jsonify({"error": "Item not found"}), 404

# Registra interesse em uma categoria
@app.route('/interests', methods=['POST'])
def post_interest():
    new_interest = request.get_json()

    interests = register_interest(new_interest)
    if interests:
        return jsonify(interests), 201

    return jsonify({"error": "Bad Request"}), 400

# Remove interesse em uma categoria
@app.route('/interests', methods=['DELETE'])
def delete_interest():
    target_interest = request.get_json()

    interests = remove_interest(target_interest)

    if interests:
        return jsonify(interests), 201

    return jsonify({"error": "Bad Request"}), 400

if __name__ == '__main__':
    app.run(debug=True)
