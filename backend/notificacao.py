import sys
import json
from shared.security import load_public_key, verify_and_extract_envelope
from cryptography.exceptions import InvalidSignature
from shared.messaging import RabbitMQHandler

PROMOTION_PUBLIC_KEY_PATH = "keys/promocao_public_key.pem"
RANKING_PUBLIC_KEY_PATH = "keys/ranking_public_key.pem"

promotion_public_key = load_public_key(PROMOTION_PUBLIC_KEY_PATH)
ranking_public_key = load_public_key(RANKING_PUBLIC_KEY_PATH)

broker = RabbitMQHandler()
broker.establish_connection()

def process_event(ch, method, properties, body):
    try:
        envelope = json.loads(body)
        incoming_routing_key = method.routing_key
        
        if incoming_routing_key == "promocao.publicada":
            event_data = verify_and_extract_envelope(envelope, promotion_public_key)
            category = event_data['categoria']
            
            public_routing_key = f"promocao.{category}"
            public_message = {
                "Título": "Nova Promoção!",
                "Produto": event_data['produto'],
                "Preço": event_data['preco']
            }
            broker.publish_message(public_routing_key, public_message)
            print(f"[+] Nova promoção {category} encaminhada para {public_routing_key}")
            
        elif incoming_routing_key == "promocao.destaque":
            event_data = verify_and_extract_envelope(envelope, ranking_public_key)
            
            category = event_data['categoria']
            score = event_data['pontuacao']
            
            public_routing_key = f"promocao.{category}"
            public_message = {
                "Título": "HOT DEAL",
                "Mensagem": f"Uma promoção da categoria {category} está em alta com {score} votos!",
                "Produto": event_data['produto'],
                "Preço": event_data['preco']
            }
            broker.publish_message(public_routing_key, public_message)
            print(f"[*] Promoção Hot Deal {category} encaminhada para {public_routing_key}")

    except InvalidSignature:
        print("\n[!] Assinatura inválida detectada! Descartando.")
    except Exception as e:
        print(f"\n[!] Erro processando o evento: {e}")

if __name__ == "__main__":
    print("[*] Iniciando Microsserviço Notificação...")
    queue_name = broker.declare_queue()
    
    broker.bind_keys(queue_name, ["promocao.publicada", "promocao.destaque"])
    
    try:
        broker.start_consuming(queue_name, process_event)
    except KeyboardInterrupt:
        print("\nAbortando...")
        broker.close_connection()
        sys.exit(0)