import uuid
from threading import Lock
from backend.shared.security import (
    load_private_key,
    load_public_key,
    verify_and_extract_envelope,
    create_signed_envelope
)
from backend.shared.messaging import RabbitMQHandler

class SharedState:
    def __init__(self):
        self.published_promos = {}
        self.hotdeal_promos = {}
        self.interests = {}

        self._lock = Lock()

        self._load_keys()
        self._start_publisher_broker()

    def _load_keys(self):
        self.private_key = load_private_key("backend/keys/gateway_private_key.pem")
        self.promocao_public_key = load_public_key("backend/keys/promocao_public_key.pem")
        self.ranking_public_key = load_public_key("backend/keys/ranking_public_key.pem")
        self.notificacao_public_key = load_public_key("backend/keys/notificacao_public_key.pem")
    
    def _start_publisher_broker(self):
        self.publisher_broker = RabbitMQHandler()
        self.publisher_broker.establish_connection()

    def get_promotions(self):
        with self._lock:
            return self.published_promos

    def add_promotion(self, new_promo):
        with self._lock:
            try:
                promo_id = new_promo["id"]
                assert promo_id not in self.published_promos.keys()
                self.published_promos[promo_id] = new_promo

            except (KeyError, AssertionError):
                print("[!] Chave de promoção inválida")
    
    def add_vote(self, promo_id, vote):
        with self._lock:
            try:
                target_promo = self.published_promos[promo_id]
            except KeyError:
                print("[!] Promoção Selecionada Inválida!")
                return {}
            
            target_promo["votos"] += vote
            return target_promo
    
    def add_hotdeal(self, promo_id, new_promo):
        with self._lock:
            self.hotdeal_promos[promo_id] = new_promo
    
    def add_interest(self, client_id, new_interest):
        with self._lock:
            if client_id in self.interests:
                if new_interest not in self.interests:
                    self.interests[client_id].append(new_interest)
                else:
                    print(f"[*] Interesse já existe para o cliente: {client_id}")
            else:
                self.interests[client_id] = [new_interest]    

            return self.interests[client_id]

    def remove_interest(self, client_id, target_interest):
        with self._lock:
            if client_id in self.interests:
                if target_interest in self.interests[client_id]:
                    self.interests[client_id].remove(target_interest)
                    return self.interests[client_id]
                
                print(f"[!] Interesse não encontrado para o cliente: {client_id}")
                return {}
            
            print(f"[!] Cliente inválido: {client_id}")
            return {}