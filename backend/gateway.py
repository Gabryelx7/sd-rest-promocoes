import json
import sys
import uuid
import threading
from cryptography.exceptions import InvalidSignature
from backend.shared.security import (
    load_private_key,
    load_public_key,
    verify_and_extract_envelope,
    create_signed_envelope
)
from backend.shared.messaging import RabbitMQHandler

PRIVATE_KEY_PATH = "backend/keys/gateway_private_key.pem"
PROMOCAO_PUBLIC_KEY_PATH = "backend/keys/promocao_public_key.pem"

private_key = load_private_key(PRIVATE_KEY_PATH)
promocao_public_key = load_public_key(PROMOCAO_PUBLIC_KEY_PATH)

promocoes_publicadas = {}
promocoes_destaque = {}
interesses = {}

publisher_broker = RabbitMQHandler()
publisher_broker.establish_connection()

# --- Thread do Consumidor ---
def consumer():
    consumer_broker = RabbitMQHandler()
    consumer_broker.establish_connection()
    queue_name = consumer_broker.declare_queue()

    consumer_broker.bind_keys(queue_name, ["promocao.publicada"])

    def callback(ch, method, properties, body):
        try:
            envelope = json.loads(body)
            event_data = verify_and_extract_envelope(envelope, promocao_public_key)
            
            promocao_id = event_data['id']
            promocoes_publicadas[promocao_id] = event_data
        
        except InvalidSignature:
            print("\n[!] Promoção publicada com assinatura inválida. Descartando.")
        except Exception as e:
            print(f"\n[!] Erro ao validar envelope: {e}")
    
    consumer_broker.start_consuming(queue_name, callback)

consumer_thread = threading.Thread(target=consumer, daemon=True)
consumer_thread.start()

# --- Métodos Chamáveis ---
def list_promotions() -> dict:
    print("\n--- Promoções Publicadas ---")
    if not promocoes_publicadas:
        print("Nenhuma promoção foi publicada ainda")
        return {}
    
    return promocoes_publicadas

def register_promotion(new_promo: dict) -> dict:
    print("\n--- Cadastro de Promoção ---")

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
    }

    envelope = create_signed_envelope(event_data, private_key)

    routing_key = "promocao.recebida"
    publisher_broker.publish_message(routing_key, envelope)

    print(f"\n[+] Promoção para '{product_name}' recebida!")
    return event_data

def vote_on_promotion(promo_id: str, request_data: dict) -> dict:
    try:
        promo = promocoes_publicadas["promo_id"]
    except IndexError:
        print("Nenhuma promoção encontrada para o ID fornecido!")
        return {}
    
    try:
        vote = int(request_data["voto"])
        assert vote == 1 or vote == -1
    except Exception:
        print("Voto inválido!")
        return {}

    event_data = {
        "id": promo_id,
        "categoria": promo['categoria'],
        "produto": promo['produto'],
        "preco": promo['preco'],
        "voto": vote
    }

    envelope = create_signed_envelope(event_data, private_key)
    publisher_broker.publish_message("promocao.voto", envelope)

    print(f"[+] Voto {vote} submetido para '{promo['produto']}'.")
    return event_data

def register_interest(request_data: dict):
    if "X-Client-Id" in request_data and "interest" in request_data:
        client_id = request_data["X-Client-Id"]
        new_interest = request_data["interest"]
        
        if client_id in interesses and new_interest not in interesses[client_id]:
            interesses[client_id].append(new_interest)
        else:
            interesses[client_id] = [new_interest]
        
        return interesses[client_id]
    
    return {}

def remove_interest(request_data: dict):
    if "X-Client-Id" in request_data and "interest" in request_data:
        client_id = request_data["X-Client-Id"]
        target_interest = request_data["interest"]

        if client_id in interesses and target_interest in interesses[client_id]:
            interesses[client_id].remove(target_interest)
            return interesses[client_id]
    
    return {}

# if __name__ == "__main__":
#     try:
#         start_api()
#     except KeyboardInterrupt:
#         print("\nAbortando...")
#         publisher_broker.close_connection()
#         sys.exit(0)
