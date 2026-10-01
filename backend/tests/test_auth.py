import pytest
from app.core.security import get_password_hash, verify_password, create_access_token, decode_token

def test_password_hashing():
    pwd = "securepassword123"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_jwt_token():
    token = create_access_token(subject=1, role="Logistics Manager")
    payload = decode_token(token)
    assert payload is not None
    assert payload.get("sub") == "1"
    assert payload.get("role") == "Logistics Manager"
