import requests, json, base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization

def verify_payload():
    url = "https://singular-snickerdoodle-de09f9.netlify.app/payload.json"
    r = requests.get(url, timeout=5)
    data = r.json()
    payload_bytes = base64.b64decode(data["payload"])
    signature = base64.b64decode(data["sig"])

    public_key_pem = b"""-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEdoUvlLjynhTV+MUNR6MhuBofhAfV
tzviR3OO8ugwD2m1V28R8NxJfhDrf76q36Fn4wCN7WSMDmbTfKB8/hB08A==
-----END PUBLIC KEY-----"""

    public_key = serialization.load_pem_public_key(public_key_pem)
    public_key.verify(signature, payload_bytes, ec.ECDSA(hashes.SHA256()))

    payload = json.loads(payload_bytes)
    return payload.get("allow", False)