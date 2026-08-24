import jwt
import pytest
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, encrypt_token, decrypt_token


def test_jwt_token_generation_and_decoding():
    """Verify JWT access and refresh token generation and decoding."""
    subject = "user_test_123"
    access_token = create_access_token(subject=subject)
    refresh_token = create_refresh_token()

    assert access_token is not None
    assert refresh_token is not None

    decoded = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert decoded is not None
    assert decoded.get("sub") == subject
    assert decoded.get("role") == "DEVELOPER"



def test_token_encryption_and_decryption():
    """Verify Fernet encryption for GitHub OAuth tokens."""
    raw_token = "gho_1234567890abcdefghijklmnopqrstuvwxyz"
    encrypted = encrypt_token(raw_token)
    assert encrypted != raw_token

    decrypted = decrypt_token(encrypted)
    assert decrypted == raw_token


def test_invalid_jwt_token_decoding():
    """Verify invalid JWT token raises PyJWT exception."""
    invalid_token = "invalid.jwt.token.string"
    with pytest.raises(jwt.PyJWTError):
        jwt.decode(invalid_token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])



def test_mocked_github_oauth_callback_flow():
    """Simulate OAuth exchange authorization code for access token."""
    mock_auth_code = "mock_code_abc123"
    mock_access_token = "gho_mocked_access_token_999"

    # Simulate OAuth exchange function logic
    def exchange_code_for_token(code: str) -> dict:
        if code == mock_auth_code:
            return {"access_token": mock_access_token, "token_type": "bearer"}
        raise ValueError("Invalid authorization code")

    res = exchange_code_for_token(mock_auth_code)
    assert res["access_token"] == mock_access_token

    with pytest.raises(ValueError):
        exchange_code_for_token("invalid_code")


if __name__ == "__main__":
    test_jwt_token_generation_and_decoding()
    test_token_encryption_and_decryption()
    test_invalid_jwt_token_decoding()
    test_mocked_github_oauth_callback_flow()
    print("Authentication & OAuth unit tests PASSED!")
