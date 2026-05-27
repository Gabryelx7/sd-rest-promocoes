import sys
import json
from src.shared.security import (
    load_private_key,
    load_public_key,
    verify_and_extract_envelope,
    create_signed_envelope
)
from src.shared.messaging import RabbitMQHandler

PRIVATE_KEY_PATH = "keys/promocao_private_key.pem"
GATEWAY_PUBLIC_KEY_PATH = "keys/gateway_public_key.pem"

private_key = load_private_key(PRIVATE_KEY_PATH)
gateway_public_key = load_public_key(GATEWAY_PUBLIC_KEY_PATH)

broker = RabbitMQHandler()
broker.establish_connection()

def process_received_promotion(ch, method, properties, body):
    try:
        envelope = json.loads(body)

        event_data = verify_and_extract_envelope(envelope, gateway_public_key)
        print(f"\nAssinatura do gateway validada. Processando promoção: {event_data['produto']}")

        new_envelope = create_signed_envelope(event_data, private_key)
        routing_key = "promocao.publicada"
        broker.publish_message(routing_key, new_envelope)
        print(f"[+] Promocao publicada para {routing_key}")

    except Exception as e:
        print(f"\n[!] Erro processando a mensagem: {e}")

if __name__ == "__main__":
    print("[*] Iniciando Microsserviço Promocao...")
    queue_name = broker.declare_queue()
    broker.bind_keys(queue_name, ["promocao.recebida"])

    try:
        broker.start_consuming(queue_name, process_received_promotion)
    except KeyboardInterrupt:
        print("\nAbortando...")
        broker.close_connection()
        sys.exit(0)
