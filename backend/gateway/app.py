import os
import sys
import threading
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from backend.gateway.sse import sse
from backend.gateway.state import SharedState
from backend.gateway.consumer import consumer
from backend.gateway.service import (
    list_promotions,
    register_promotion,
    vote_on_promotion,
    register_interest,
    remove_interest,
    list_interests
)
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

load_dotenv()

app.config["REDIS_URL"] = os.getenv("REDIS_URL")

@app.after_request
def add_cors_headers(response):
    response.headers.setdefault("Access-Control-Allow-Origin", "*")
    response.headers.setdefault("Access-Control-Allow-Headers", "Content-Type,Authorization,X-Requested-With,X-Client-Id")
    response.headers.setdefault("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
    return response

app.register_blueprint(sse, url_prefix='/stream')

state_object = SharedState()

# Lista promoções
@app.route('/promotions', methods=['GET'])
def get_promotions():
    client_id = request.headers.get("X-Client-Id")
    published_promos = list_promotions(state_object)
    
    if not client_id:
        return jsonify(published_promos), 200

    user_interests = list_interests(state_object, client_id) or []
    hotdeals = state_object.hotdeal_promos
    
    filtered_promos = {}
    for pid, promo in published_promos.items():
        if promo.get("categoria") in user_interests or pid in hotdeals:
            filtered_promos[pid] = promo
    
    return jsonify(filtered_promos), 200

# Cadastra uma nova promoção
@app.route('/promotions', methods=['POST'])
def post_promotion():
    request_body = request.get_json()
    new_promo = register_promotion(state_object, request_body)
    if new_promo:
        return jsonify(new_promo), 201
    
    return jsonify(new_promo), 400

# Vota em uma promoção
@app.route('/promotions/<string:promo_id>', methods=['POST'])
def vote_promotion_route(promo_id):
    request_body = request.get_json()
    updated_promo = vote_on_promotion(state_object, promo_id, request_body)
    if updated_promo:
        return jsonify(updated_promo), 201
    
    return jsonify({"error": "Item not found"}), 404

# Registra interesse em uma categoria
@app.route('/interests', methods=['POST'])
def post_interest():
    request_body = request.get_json() or {}
    client_id = request.headers.get("X-Client-Id")

    if not client_id:
        return jsonify({"error": "Missing X-Client-Id header"}), 400

    request_body["X-Client-Id"] = client_id

    interests_list = register_interest(state_object, request_body)
    if interests_list is not None and interests_list != {}:
        return jsonify(interests_list), 201

    return jsonify({"error": "Bad Request"}), 400

# Remove interesse em uma categoria
@app.route('/interests', methods=['DELETE'])
def delete_interest():
    request_body = request.get_json() or {}
    client_id = request.headers.get("X-Client-Id")
    
    if not client_id:
        return jsonify({"error": "Missing X-Client-Id header"}), 400

    request_body["X-Client-Id"] = client_id

    interests = remove_interest(state_object, request_body)
    if interests is not None and interests != {}:
        return jsonify(interests), 200

    return jsonify({"error": "Bad Request"}), 400

# Lista os interesses de um usuário
@app.route('/interests', methods=['GET'])
def get_interests():
    client_id = request.headers.get("X-Client-Id")
    if not client_id:
        return jsonify({"error": "Missing X-Client-Id header"}), 400

    interests = list_interests(state_object, client_id)
    if interests is not None and interests != {}:
        return jsonify(interests), 200

    return jsonify({"error": "Bad Request"}), 400

if __name__ == "__main__":
    consumer_thread = threading.Thread(target=consumer, args=(state_object, app), daemon=True)
    consumer_thread.start()
    try:
        app.run(threaded=True, use_reloader=False)
    except Exception as e:
        print("\nAbortando...")
        print(f"Erro: {e}")
        sys.exit(0)