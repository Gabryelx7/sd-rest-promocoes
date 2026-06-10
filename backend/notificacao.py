import os
import sys
import json
import resend
from backend.shared.security import load_public_key, verify_and_extract_envelope
from backend.shared.messaging import RabbitMQHandler
from cryptography.exceptions import InvalidSignature
from dotenv import load_dotenv

load_dotenv()

PROMOTION_PUBLIC_KEY_PATH = "backend/keys/promocao_public_key.pem"
RANKING_PUBLIC_KEY_PATH = "backend/keys/ranking_public_key.pem"

promotion_public_key = load_public_key(PROMOTION_PUBLIC_KEY_PATH)
ranking_public_key = load_public_key(RANKING_PUBLIC_KEY_PATH)

resend.api_key = os.getenv("RESEND_API_KEY")
resend_account_email = os.getenv("RESEND_EMAIL")

broker = RabbitMQHandler()
broker.establish_connection()

def send_store_email(to_email, subject, html_content):
    if not resend.api_key:
        print("[!] Alerta: RESEND_API_KEY não configurada. Ignorando envio de email.")
        return

    if to_email != resend_account_email:
        print("[!] Alerta: E-mail inválido! Utilize o email configurado no Resend.")
        return

    try:
        params: resend.Emails.SendParams = {
            "from": "Promoções <onboarding@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        resend.Emails.send(params)
        print(f"[+] Email enviado com sucesso para {to_email}!")
    except Exception as e:
        print(f"[!] Falha ao interagir com API do Resend: {e}")

def process_event(ch, method, properties, body):
    try:
        envelope = json.loads(body)
        incoming_routing_key = method.routing_key
        
        if incoming_routing_key == "promocao.publicada":
            event_data = verify_and_extract_envelope(envelope, promotion_public_key)
            category = event_data['categoria']
            store_email = event_data['email_loja']
            
            public_routing_key = f"promocao.categoria.{category}"
            public_message = {
                "Título": "Nova Promoção!",
                "Produto": event_data['produto'],
                "Preço": event_data['preco']
            }
            broker.publish_message(public_routing_key, public_message)
            print(f"[+] Nova promoção {category} encaminhada para {public_routing_key}")

            if store_email:
                subject = f"Promoção Aprovada: {event_data['produto']}"
                html = f"""
                <h3>Sua promoção foi aprovada e já está no ar!</h3>
                <p><b>Produto:</b> {event_data['produto']}</p>
                <p><b>Preço:</b> R$ {event_data['preco']:.2f}</p>
                <p><b>Categoria:</b> {category}</p>
                """
                send_store_email(store_email, subject, html)
        
        elif incoming_routing_key == "promocao.destaque":
            event_data = verify_and_extract_envelope(envelope, ranking_public_key)
            store_email = event_data.get('email_loja')
            
            print(f"[*] Processando Destaque para o ranking da promoção {event_data['id'][:8]}")

            if store_email:
                subject = f"PARABÉNS! Seu produto está em DESTAQUE: {event_data['produto']}"
                html = f"""
                <h3>Seu produto virou um Hot Deal!</h3>
                <p>O produto <b>{event_data['produto']}</b> acabou de atingir a marca de <b>{event_data['pontuacao']} votos positivos</b> e está em destaque na página principal!</p>
                """
                send_store_email(store_email, subject, html)

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