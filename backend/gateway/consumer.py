import json
from backend.shared.security import verify_and_extract_envelope
from backend.shared.messaging import RabbitMQHandler
from backend.gateway.state import SharedState
from cryptography.exceptions import InvalidSignature
from flask_sse import sse

def consumer(shared_state: SharedState):
    consumer_broker = RabbitMQHandler()
    consumer_broker.establish_connection()
    queue_name = consumer_broker.declare_queue()

    consumer_broker.bind_keys(
        queue_name,
        [
            "promocao.publicada", 
            "promocao.destaque",
            "promocao.categoria.*"
        ]
    )

    def callback(ch, method, properties, body):
        from backend.app import app
        try:
            envelope = json.loads(body)
            incoming_routing_key = method.routing_key

            if incoming_routing_key == "promocao.publicada":
                event_data = verify_and_extract_envelope(envelope, shared_state.promocao_public_key)
                shared_state.add_promotion(event_data)

            elif incoming_routing_key == "promocao.destaque":
                event_data = verify_and_extract_envelope(envelope, ranking_public_key)
                category = event_data['categoria']
                score = event_data['pontuacao']
                pub_message = {
                    "Título": "HOT DEAL",
                    "Mensagem": f"Uma promoção da categoria {category} está em alta com {score} votos!",
                    "Produto": event_data['produto'],
                    "Preço": event_data['preco']
                }
                with app.app_context():
                    sse.publish(pub_message, type='hotdeal')
                print("Hot Deal message sent!")

            elif incoming_routing_key.startswith("promocao.categoria."):
                event_data = verify_and_extract_envelope(envelope, notificacao_public_key)
                category = incoming_routing_key.split('.')[-1]
                pub_message = event_data
                with app.app_context():
                    sse.publish(pub_message, type='category')
                print("Category message sent!")

        except InvalidSignature:
            print("\n[!] Promoção publicada com assinatura inválida. Descartando.")
        except Exception as e:
            print(f"\n[!] Erro ao validar envelope: {e}")
    consumer_broker.start_consuming(queue_name, callback)