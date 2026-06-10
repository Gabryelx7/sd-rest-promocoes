"""
Métodos Chamáveis pela API
"""

import uuid
from backend.gateway.state import SharedState
from backend.shared.security import create_signed_envelope
from backend.shared.messaging import RabbitMQHandler

def list_promotions(shared_state: SharedState) -> dict:
    published_promos = shared_state.get_promotions()
    if not published_promos:
        print("Nenhuma promoção foi publicada ainda")
        return {}
    return published_promos

def register_promotion(shared_state: SharedState, new_promo: dict) -> dict:
    try:
        product_name = new_promo["produto"]
        category = new_promo["categoria"]
        price = float(new_promo["preco"])
    except Exception:
        return {}

    event_data = {
        "id": str(uuid.uuid4()),
        "produto": product_name,
        "categoria": category,
        "preco": price,
        "votos": 0
    }

    envelope = create_signed_envelope(event_data, shared_state.private_key)

    publisher = RabbitMQHandler()
    publisher.establish_connection()
    publisher.publish_message("promocao.recebida", envelope)
    publisher.close_connection()

    print(f"\n[+] Promoção para '{product_name}' recebida!")
    return event_data

def vote_on_promotion(shared_state: SharedState, promo_id: str, request_data: dict) -> dict:
    try:
        vote = int(request_data["voto"])
        assert vote == 1 or vote == -1
    except (AssertionError, TypeError, KeyError):
        print("[!] Voto inválido!")
        return {}
    
    updated_promo = shared_state.add_vote(promo_id, vote)
    if not updated_promo:
        return {}

    event_data = {
        "id": promo_id,
        "categoria": updated_promo['categoria'],
        "produto": updated_promo['produto'],
        "preco": updated_promo['preco'],
        "voto": vote
    }
    
    envelope = create_signed_envelope(event_data, shared_state.private_key)

    publisher = RabbitMQHandler()
    publisher.establish_connection()
    publisher.publish_message("promocao.voto", envelope)
    publisher.close_connection()

    print(f"[+] Voto de {vote} enviado para a promoção {promo_id[:8]}")
    return updated_promo

def register_interest(shared_state: SharedState, request_data: dict):
    if "X-Client-Id" in request_data and "interesse" in request_data:
        client_id = request_data["X-Client-Id"]
        new_interest = request_data["interesse"]

        interests_list = shared_state.add_interest(client_id, new_interest)
        return interests_list
    
    return {}

def remove_interest(shared_state: SharedState, request_data: dict):
    if "X-Client-Id" in request_data and "interesse" in request_data:
        client_id = request_data["X-Client-Id"]
        target_interest = request_data["interesse"]

        interests_list = shared_state.remove_interest(client_id, target_interest)
        return interests_list
    
    return {}
