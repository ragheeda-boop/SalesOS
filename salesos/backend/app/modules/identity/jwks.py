from __future__ import annotations

import base64
import logging
import os
from typing import Any

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.config import settings

logger = logging.getLogger("salesos.jwks")

_RSA_KEY_DIR = os.environ.get(
    "SALESOS_JWKS_KEY_DIR",
    os.path.join(os.path.dirname(__file__), "_keys"),
)
_RSA_PRIVATE_PATH = os.path.join(_RSA_KEY_DIR, "rsa_private.pem")
_RSA_PUBLIC_PATH = os.path.join(_RSA_KEY_DIR, "rsa_public.pem")
_KID = "v2-rs256"


def _encryption_passphrase() -> bytes:
    return settings.secret_key.encode("utf-8")


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _allow_regeneration() -> bool:
    return os.environ.get("SALESOS_JWKS_ALLOW_REGENERATE", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _load_or_generate_rsa() -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    private_path = _RSA_PRIVATE_PATH
    public_path = _RSA_PUBLIC_PATH

    if os.path.exists(private_path) and os.path.exists(public_path):
        with open(public_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())
        with open(private_path, "rb") as f:
            private_data = f.read()
        # Try encrypted first, fall back to unencrypted for migration.
        try:
            private_key = serialization.load_pem_private_key(
                private_data, password=_encryption_passphrase(), backend=default_backend()
            )
            logger.info("JWKS RSA keys loaded successfully (encrypted)")
            return private_key, public_key
        except (ValueError, TypeError):
            pass
        try:
            private_key = serialization.load_pem_private_key(
                private_data, password=None, backend=default_backend()
            )
            logger.warning(
                "JWKS private key was unencrypted — re-saving with SECRET_KEY encryption"
            )
            _save_private_key(private_path, private_key)
            return private_key, public_key
        except (ValueError, TypeError):
            if not _allow_regeneration():
                raise RuntimeError(
                    "RSA private key is encrypted but SECRET_KEY cannot decrypt it. "
                    "Use an isolated JWKS volume (virtual staging) or set "
                    "SALESOS_JWKS_ALLOW_REGENERATE=1 to mint new keys for this env."
                ) from None
            logger.critical(
                "JWKS KEY REGENERATION TRIGGERED — existing key cannot be decrypted "
                "with current SECRET_KEY. All previously issued tokens will become invalid. "
                "Key dir: %s",
                _RSA_KEY_DIR,
            )

    os.makedirs(_RSA_KEY_DIR, exist_ok=True)

    logger.warning("Generating new RSA-4096 JWKS keypair in %s", _RSA_KEY_DIR)
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend(),
    )
    public_key = private_key.public_key()

    _save_private_key(private_path, private_key)

    with open(public_path, "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )

    return private_key, public_key


def _save_private_key(path: str, private_key: rsa.RSAPrivateKey) -> None:
    try:
        with open(path, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.BestAvailableEncryption(
                        _encryption_passphrase()
                    ),
                )
            )
        os.chmod(path, 0o600)
    except PermissionError:
        logger.warning(
            "Cannot persist JWKS private key to %s (permission denied). "
            "Keys will be regenerated on restart. Fix: ensure /data/jwks is "
            "owned by the salesos user.",
            path,
        )


_private_key: rsa.RSAPrivateKey | None = None
_public_key: rsa.RSAPublicKey | None = None
_jwks_cache: dict[str, Any] | None = None


def _ensure_keys():
    global _private_key, _public_key, _jwks_cache
    if _private_key is None:
        _private_key, _public_key = _load_or_generate_rsa()
        _jwks_cache = None


def get_private_key() -> rsa.RSAPrivateKey:
    _ensure_keys()
    return _private_key


def get_public_key() -> rsa.RSAPublicKey:
    _ensure_keys()
    return _public_key


def get_jwks() -> dict[str, list[dict[str, Any]]]:
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    _ensure_keys()
    pub_numbers = _public_key.public_numbers()

    # RFC 7517 JWK representation of RSA public key
    n = _b64url(pub_numbers.n.to_bytes((pub_numbers.n.bit_length() + 7) // 8, "big"))
    e = _b64url(pub_numbers.e.to_bytes((pub_numbers.e.bit_length() + 7) // 8, "big"))

    jwk = {
        "kty": "RSA",
        "kid": _KID,
        "alg": "RS256",
        "use": "sig",
        "n": n,
        "e": e,
    }

    _jwks_cache = {"keys": [jwk]}
    return _jwks_cache


def create_rs256_token_payload(payload: dict) -> str:
    from jose import jwt

    private_key = get_private_key()
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    token_payload = {**payload, "kid": _KID}
    return jwt.encode(token_payload, pem_private, algorithm="RS256")


def decode_token(token: str) -> dict:
    from jose import JWTError, jwt

    public_key = get_public_key()
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    try:
        return jwt.decode(
            token,
            pem_public,
            algorithms=["RS256"],
            audience="salesos-api",
        )
    except JWTError:
        raise ValueError("Invalid or expired token") from None
