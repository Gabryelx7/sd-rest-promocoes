from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

KEYS = ["promocao", "ranking", "gateway", "notificacao"]

for key in KEYS:
    PRIVATE_KEY_FILE = f"keys/{key}_private_key.pem"
    PUBLIC_KEY_FILE = f"keys/{key}_public_key.pem"

    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    with open(PRIVATE_KEY_FILE, "wb") as f:
        f.write(private_pem)
    print(f"Chave privada salva em: {PRIVATE_KEY_FILE}")

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    with open(PUBLIC_KEY_FILE, "wb") as f:
        f.write(public_pem)
    print(f"Chave pública salva em: {PUBLIC_KEY_FILE}")
