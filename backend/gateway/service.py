"""
Métodos Chamáveis pela API
"""

import uuid
from backend.gateway.state import SharedState
from backend.shared.security import (
    create_signed_envelope,
    verify_and_extract_envelope
)
from backend.shared.messaging import RabbitMQHandler
from cryptography.exceptions import InvalidSignature

def list_promotions(shared_state: SharedState) -> dict:
    published_promos = shared_state.get_promotions()
    if not published_promos:
        print("Nenhuma promoção foi publicada ainda")
        return {}
    return published_promos

def register_promotion(shared_state: SharedState, request_envelope: dict) -> dict:
    try:
        store_data = verify_and_extract_envelope(request_envelope, shared_state.loja_public_key)

        product_name = store_data["produto"]
        category = store_data["categoria"]
        price = float(store_data["preco"])
        email_loja = store_data["email_loja"]
    except InvalidSignature:
        print("[!] Assinatura da LOJA inválida rejeitada via HTTP API!")
        return {"error": "Assinatura digital inválida."}
    except Exception as e:
        print(f"[!] Erro de payload: {e}")
        return {}

    event_data = {
        "id": str(uuid.uuid4()),
        "produto": product_name,
        "categoria": category,
        "preco": price,
        "email_loja": email_loja,
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
        return {"error": "Invalid vote"}
    
    updated_promo = shared_state.add_vote(promo_id, vote)
    if not updated_promo:
        return {"error": "Item not found"}

    event_data = {
        "id": promo_id,
        "categoria": updated_promo['categoria'],
        "produto": updated_promo['produto'],
        "preco": updated_promo['preco'],
        "email_loja": updated_promo['email_loja'],
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

def list_interests(shared_state: SharedState, client_id: str):
    interests_list = shared_state.get_interests(client_id)
    
    return interests_list
