import json
import sys
import uuid
import threading
import time
from cryptography.exceptions import InvalidSignature
from src.shared.security import (
    load_private_key,
    load_public_key,
    verify_and_extract_envelope,
    create_signed_envelope
)
from src.shared.messaging import RabbitMQHandler

PRIVATE_KEY_PATH = "keys/gateway_private_key.pem"
PROMOCAO_PUBLIC_KEY_PATH = "keys/promocao_public_key.pem"

private_key = load_private_key(PRIVATE_KEY_PATH)
promocao_public_key = load_public_key(PROMOCAO_PUBLIC_KEY_PATH)

promocoes_publicadas = {}

publisher_broker = RabbitMQHandler()
publisher_broker.establish_connection()

# --- Thread do Consunidor ---
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

# --- Meu Principal ---
def menu():
    time.sleep(0.5)
    while True:
        print("\n=== Sistema de Promoções - Gateway ===")
        print("1. Cadastrar uma nova promoção")
        print("2. Listar as promoções")
        print("3. Votar nas promoções")
        print("4. Sair")

        choice = input("Selecione uma opção: ")

        if choice == '1':
            register_promotion()
        elif choice == '2':
            list_promotions()
        elif choice == '3':
            vote_on_promotions()
        elif choice == '4':
            print("Fechando a conexão...")
            publisher_broker.close_connection()
            sys.exit(0)
        else:
            print("Opção inválida. Tente novamente")

def register_promotion():
    print("\n--- Cadastro de Promoção ---")
    
    product_name = input("Nome do Produto: ")
    category = input("Categoria: ")
    price = float(input("Preço: "))

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

def list_promotions():
    print("\n--- Promoções Publicadas ---")
    if not promocoes_publicadas:
        print("Nenhuma promoção foi publicada ainda")
        return
    
    for id, promo in promocoes_publicadas.items():
        print(f"- {promo['produto']} ({promo['categoria']}) : {promo['preco']}R$")

def vote_on_promotions():
    while True:
        print("\n--- Vote em uma Promoção---")
        if not promocoes_publicadas:
            print("Nenhuma promoção foi publicada ainda")
            return
        
        promo_list = list(promocoes_publicadas.items())
        for i, (promo_id, promo) in enumerate(promo_list, start=1):
            print(f"{i}. {promo['produto']} ({promo['categoria']}) : {promo['preco']}R$")
        
        print("0. Retornar ao menu principal")
        print("-"*30)

        choice = input("Digite o número da promoção escolhida: ").strip()
        
        try:
            choice = int(choice)
        except ValueError:
            print("[!] Seleção inválida. Tente novamente.")
            continue
        
        if choice == 0:
            return
        elif choice < 0 or choice > len(promo_list):
            print("[!] Número inválido. Tente novamente.")
            continue

        promo_id = promo_list[choice-1][0]
        product_name = promo_list[choice-1][1]['produto']

        vote = input(f"Votando em '{product_name}' (+1 para positivo, -1 para negativo, 0 para cancelar): ").strip()
        if vote == '0':
            continue
        if vote not in ['+1', '-1']:
            print("[!] Voto inválido. Tente novamente")
            continue

        event_data = {
            "id": promo_id,
            "categoria": promo['categoria'],
            "produto": promo['produto'],
            "preco": promo['preco'],
            "voto": int(vote)
        }

        envelope = create_signed_envelope(event_data, private_key)
        publisher_broker.publish_message("promocao.voto", envelope)

        print(f"[+] Voto {vote} submetido para '{product_name}'.")
        time.sleep(0.5)
    


if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\nAbortando...")
        publisher_broker.close_connection()
        sys.exit(0)

