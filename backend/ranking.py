# src/ranking.py
import sys
import json
from shared.security import (
    load_private_key,
    load_public_key,
    verify_and_extract_envelope,
    create_signed_envelope
)
from cryptography.exceptions import InvalidSignature
from shared.messaging import RabbitMQHandler

PRIVATE_KEY_PATH = "keys/ranking_private_key.pem"
GATEWAY_PUBLIC_KEY_PATH = "keys/gateway_public_key.pem"
HOT_DEAL_THRESHOLD = 3

private_key = load_private_key(PRIVATE_KEY_PATH)
gateway_public_key = load_public_key(GATEWAY_PUBLIC_KEY_PATH)

broker = RabbitMQHandler()
broker.establish_connection()

promotion_scores = {}
hot_deal_promotions = set()

def process_vote(ch, method, properties, body):
    try:
        envelope = json.loads(body)
        
        event_data = verify_and_extract_envelope(envelope, gateway_public_key)
        
        promo_id = event_data['id']
        vote_value = event_data['voto']
        
        current_score = promotion_scores.get(promo_id, 0)
        new_score = current_score + vote_value
        promotion_scores[promo_id] = new_score
        
        print(f"[+] Voto recebido. Nova pontuação da promoção de ID {promo_id[:8]}...: {new_score}")
        
        if new_score >= HOT_DEAL_THRESHOLD and promo_id not in hot_deal_promotions:
            print(f"[*] Pontuação atingiu o limite! Promovendo {promo_id[:8]}... para Hot Deal.")
            hot_deal_promotions.add(promo_id)
            
            hot_deal_data = {
                "id": promo_id,
                "categoria": event_data['categoria'],
                "produto": event_data['produto'],
                "preco": event_data['preco'],
                "pontuacao": new_score
            }
            
            hot_deal_envelope = create_signed_envelope(hot_deal_data, private_key)
            broker.publish_message("promocao.destaque", hot_deal_envelope)
            print(f"[+] Promoção publicada para promocao.destaque")
            
    except InvalidSignature:
        print("\n[!] Assinatura inválida detectada no voto! Descartando.")
    except Exception as e:
        print(f"\n[!] Erro processando o voto: {e}")

if __name__ == "__main__":
    print(f"[*] Iniciando Microsserviço Ranking...")
    queue_name = broker.declare_queue()
    broker.bind_keys(queue_name, ["promocao.voto"])
    
    try:
        broker.start_consuming(queue_name, process_vote)
    except KeyboardInterrupt:
        print("\nAbortando...")
        broker.close_connection()
        sys.exit(0)