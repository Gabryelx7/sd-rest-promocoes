from flask import Flask, jsonify, request

app = Flask(__name__)

promotions = []
interests = []

# Lista promoções
@app.route('/promotions', methods=['GET'])
def get_promotions():
    return jsonify(promotions), 200

# Cadastra uma nova promoção
@app.route('/promotions', methods=['POST'])
def post_promotion():
    new_promo = request.get_json()
    new_promo["id"] = len(promotions) + 1
    new_promo["vote"] = 0
    promotions.append(new_promo)
    return jsonify(new_promo), 201

# Retorna uma promoção específica
@app.route('/promotions/<int:promo_id>', methods=['GET'])
def get_promotion(promo_id):
    promo = next((promo for promo in promotions if promo["id"] == promo_id), None)
    if promo:
        return jsonify(promo), 200
    return jsonify({"error": "item not found"}), 404

# Vota em uma promoção
@app.route('/promotions/<int:promo_id>', methods=['PATCH'])
def vote_on_promotion(promo_id):
    updated_data = request.get_json()
    promo = next((promo for promo in promotions if promo["id"] == promo_id), None)
    if promo:
        if "vote" in updated_data and (updated_data["vote"] == 1 or updated_data["vote"] == -1):
            promo["vote"] += updated_data["vote"]
            return jsonify(promo), 200
        
        return jsonify({"error": "Bad Request"}), 400
    
    return jsonify({"error": "Item not found"}), 404

# Registra interesse em uma categoria
@app.route('/interests', methods=['POST'])
def post_interest():
    new_interest = request.get_json()
    new_interest["id"] = len(interests) + 1
    interests.append(new_interest)
    return jsonify(new_interest), 201

# Remove interesse em uma categoria
@app.route('/interests', methods=['DELETE'])
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
