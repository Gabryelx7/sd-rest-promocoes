import os
import sys
import requests
from backend.shared.security import load_private_key, create_signed_envelope
from dotenv import load_dotenv

load_dotenv()

RESEND_EMAIL = os.getenv("RESEND_EMAIL")

GATEWAY_URL = "http://127.0.0.1:5000/promotions"
STORE_PRIVATE_KEY_PATH = "backend/keys/loja_private_key.pem"

try:
    private_key = load_private_key(STORE_PRIVATE_KEY_PATH)
except FileNotFoundError:
    print(f"[!] Error: Missing {STORE_PRIVATE_KEY_PATH}")
    sys.exit(1)

def main():
    print("=== Painel da Loja - Cadastrar Promoção ===")
    while True:
        produto = input("Nome do Produto: ").strip()
        categoria = input("Categoria: ").strip().lower()
        
        try:
            preco = float(input("Preço: "))
        except ValueError:
            print("[!] Preço inválido.")
            return

        email_loja = RESEND_EMAIL

        event_data = {
            "produto": produto,
            "categoria": categoria,
            "preco": preco,
            "email_loja": email_loja
        }

        envelope = create_signed_envelope(event_data, private_key)

        print("\n[*] Enviando promoção assinada via REST API...")
        try:
            response = requests.post(GATEWAY_URL, json=envelope)
            
            if response.status_code == 201:
                print("[+] Sucesso! Promoção enviada e aceita pelo Gateway.")
                print(response.json())
            else:
                print(f"[!] Erro no Gateway ({response.status_code}): {response.json()}")
                
        except requests.exceptions.ConnectionError:
            print("[!] Erro: Não foi possível conectar ao Gateway API. Ele está rodando?")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAbortando...")
    except Exception as e:
        print(f"\nErro: {e}; Abortando...")