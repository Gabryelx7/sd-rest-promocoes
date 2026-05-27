import json
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

def load_private_key(filepath):
    with open(filepath, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def load_public_key(filepath):
    with open(filepath, "rb") as f:
        return serialization.load_pem_public_key(f.read())

def sign_event(event_data, private_key):
    message_string = json.dumps(event_data, sort_keys=True)
    message_bytes = message_string.encode('utf-8')
    
    signature_bytes = private_key.sign(message_bytes)
    
    return base64.b64encode(signature_bytes).decode('utf-8')

def verify_event_signature(event_data, signature_b64, public_key):
    message_string = json.dumps(event_data, sort_keys=True)
    message_bytes = message_string.encode('utf-8')
    
    signature_bytes = base64.b64decode(signature_b64)
    
    try:
        public_key.verify(signature_bytes, message_bytes)
        return True
    except InvalidSignature:
        return False

def create_signed_envelope(event_data, private_key):
    signature = sign_event(event_data, private_key)
    return {
        "data": event_data,
        "signature": signature
    }

def verify_and_extract_envelope(envelope, public_key):
    event_data = envelope.get("data")
    signature = envelope.get("signature")

    if not event_data or not signature:
        raise ValueError("Formato de envelope inválido")
    
    is_valid = verify_event_signature(event_data, signature, public_key)
    if not is_valid:
        raise InvalidSignature("A assinatura não é válida")
    
    return event_data