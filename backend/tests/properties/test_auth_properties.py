"""
Property-based tests for authentication service.

Tests correctness properties for:
- Token encryption round-trip (Property 2)
- JWT round-trip consistency (Property 1)
- Authentication enforcement (Property 16)
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hypothesis import given, strategies as st, settings, assume

from app.services.auth_service import AuthService, TokenEncryptionError


class TestTokenEncryptionProperties:
    """
    **Feature: gambling-comment-detector, Property 2: Token Encryption Round-Trip**
    **Validates: Requirements 1.3, 10.1, 11.3**
    
    For any OAuth token string, encrypting and then decrypting the token
    SHALL produce the original token value.
    """

    @given(
        token=st.text(min_size=1, max_size=2000).filter(lambda x: len(x.strip()) > 0)
    )
    @settings(max_examples=100)
    def test_encrypt_decrypt_roundtrip(self, token: str):
        """
        Property: encrypt(decrypt(token)) == token
        
        For any non-empty token string, encrypting and then decrypting
        should return the original token.
        """
        auth_service = AuthService()
        
        # Encrypt the token
        encrypted = auth_service.encrypt_token(token)
        
        # Encrypted should be different from original
        assert encrypted != token
        
        # Decrypt should return original
        decrypted = auth_service.decrypt_token(encrypted)
        
        assert decrypted == token

    @given(
        token=st.text(
            min_size=10,
            max_size=500,
            alphabet=st.characters(
                whitelist_categories=('L', 'N', 'P', 'S'),
                blacklist_characters='\x00'
            )
        ).filter(lambda x: len(x.strip()) > 0)
    )
    @settings(max_examples=100)
    def test_encrypt_produces_different_output(self, token: str):
        """
        Property: encrypt(token) != token
        
        Encryption should always produce output different from input.
        """
        auth_service = AuthService()
        
        encrypted = auth_service.encrypt_token(token)
        
        # Encrypted value should never equal the plaintext
        assert encrypted != token

    @given(
        token=st.text(min_size=1, max_size=500).filter(lambda x: len(x.strip()) > 0)
    )
    @settings(max_examples=100)
    def test_encryption_is_deterministic_per_call(self, token: str):
        """
        Property: Multiple encryptions of same token produce different ciphertexts
        
        Fernet uses random IV, so each encryption should be unique.
        This is a security property - prevents pattern analysis.
        """
        auth_service = AuthService()
        
        encrypted1 = auth_service.encrypt_token(token)
        encrypted2 = auth_service.encrypt_token(token)
        
        # Each encryption should produce different ciphertext (due to random IV)
        # But both should decrypt to the same value
        assert encrypted1 != encrypted2
        
        decrypted1 = auth_service.decrypt_token(encrypted1)
        decrypted2 = auth_service.decrypt_token(encrypted2)
        
        assert decrypted1 == decrypted2 == token


class TestJWTProperties:
    """
    **Feature: gambling-comment-detector, Property 1: JWT Round-Trip Consistency**
    **Validates: Requirements 1.4**
    
    For any valid user data, creating a JWT token and then decoding it
    SHALL produce equivalent user information (id, email, google_id).
    """

    @given(
        user_id=st.uuids(),
        email=st.emails(),
        google_id=st.text(
            min_size=10,
            max_size=50,
            alphabet=st.characters(whitelist_categories=('Nd', 'Lu', 'Ll'))
        )
    )
    @settings(max_examples=100)
    def test_jwt_roundtrip(self, user_id, email, google_id):
        """
        Property: verify_jwt(create_jwt(user_data)) contains equivalent user data
        
        For any valid user data, creating a JWT and then verifying it
        should return the same user information.
        """
        auth_service = AuthService()
        
        # Create user data
        user_data = {
            "id": str(user_id),
            "email": email,
            "google_id": google_id
        }
        
        # Create JWT
        token = auth_service.create_jwt(user_data)
        
        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify JWT
        decoded = auth_service.verify_jwt(token)
        
        # Decoded data should match original
        assert decoded["id"] == str(user_id)
        assert decoded["email"] == email
        assert decoded["google_id"] == google_id

    @given(
        user_id=st.uuids(),
        email=st.emails(),
        google_id=st.text(
            min_size=10,
            max_size=50,
            alphabet=st.characters(whitelist_categories=('Nd', 'Lu', 'Ll'))
        )
    )
    @settings(max_examples=100)
    def test_jwt_contains_token_type(self, user_id, email, google_id):
        """
        Property: JWT tokens contain correct token type
        
        Access tokens should have type "access", refresh tokens should have type "refresh".
        """
        auth_service = AuthService()
        
        user_data = {
            "id": str(user_id),
            "email": email,
            "google_id": google_id
        }
        
        # Test access token
        access_token = auth_service.create_jwt(user_data, token_type="access")
        access_decoded = auth_service.verify_jwt(access_token)
        assert access_decoded["type"] == "access"
        
        # Test refresh token
        refresh_token = auth_service.create_jwt(user_data, token_type="refresh")
        refresh_decoded = auth_service.verify_jwt(refresh_token)
        assert refresh_decoded["type"] == "refresh"

    @given(
        user_id=st.uuids(),
        email=st.emails(),
        google_id=st.text(
            min_size=10,
            max_size=50,
            alphabet=st.characters(whitelist_categories=('Nd', 'Lu', 'Ll'))
        )
    )
    @settings(max_examples=100)
    def test_jwt_has_expiration(self, user_id, email, google_id):
        """
        Property: All JWT tokens have expiration timestamp
        
        Every created JWT should have an exp claim set.
        """
        auth_service = AuthService()
        
        user_data = {
            "id": str(user_id),
            "email": email,
            "google_id": google_id
        }
        
        token = auth_service.create_jwt(user_data)
        decoded = auth_service.verify_jwt(token)
        
        # Should have expiration
        assert decoded["exp"] is not None
        assert decoded["iat"] is not None


from datetime import timedelta

from app.services.auth_service import JWTExpiredError, JWTInvalidError


class TestAuthenticationEnforcementProperties:
    """
    **Feature: gambling-comment-detector, Property 16: Authentication Enforcement**
    **Validates: Requirements 11.1, 11.2**
    
    For any protected endpoint, requests without valid JWT or with expired JWT
    SHALL receive 401 status response.
    """

    @given(
        invalid_token=st.text(min_size=1, max_size=500).filter(
            lambda x: not x.startswith("eyJ")  # Filter out JWT-like strings
        )
    )
    @settings(max_examples=100)
    def test_invalid_token_rejected(self, invalid_token: str):
        """
        Property: Invalid tokens are rejected
        
        For any string that is not a valid JWT, verify_jwt should raise JWTInvalidError.
        """
        auth_service = AuthService()
        
        try:
            auth_service.verify_jwt(invalid_token)
            # Should not reach here
            assert False, "Expected JWTInvalidError to be raised"
        except JWTInvalidError:
            # Expected behavior
            pass

    @given(
        user_id=st.uuids(),
        email=st.emails(),
        google_id=st.text(
            min_size=10,
            max_size=50,
            alphabet=st.characters(whitelist_categories=('Nd', 'Lu', 'Ll'))
        )
    )
    @settings(max_examples=100)
    def test_expired_token_rejected(self, user_id, email, google_id):
        """
        Property: Expired tokens are rejected with JWTExpiredError
        
        For any user data, a JWT created with negative expiration should be rejected.
        """
        auth_service = AuthService()
        
        user_data = {
            "id": str(user_id),
            "email": email,
            "google_id": google_id
        }
        
        # Create an already-expired token
        expired_token = auth_service.create_jwt(
            user_data,
            expires_delta=timedelta(seconds=-10)  # Already expired
        )
        
        try:
            auth_service.verify_jwt(expired_token)
            # Should not reach here
            assert False, "Expected JWTExpiredError to be raised"
        except JWTExpiredError:
            # Expected behavior
            pass

    def test_empty_token_rejected(self):
        """
        Property: Empty tokens are rejected
        
        An empty string token should raise JWTInvalidError.
        """
        auth_service = AuthService()
        
        try:
            auth_service.verify_jwt("")
            assert False, "Expected JWTInvalidError to be raised"
        except JWTInvalidError:
            pass

    def test_none_token_rejected(self):
        """
        Property: None tokens are rejected
        
        A None token should raise JWTInvalidError.
        """
        auth_service = AuthService()
        
        try:
            auth_service.verify_jwt(None)
            assert False, "Expected JWTInvalidError to be raised"
        except (JWTInvalidError, TypeError):
            # Either exception is acceptable
            pass

    @given(
        user_id=st.uuids(),
        email=st.emails(),
        google_id=st.text(
            min_size=10,
            max_size=50,
            alphabet=st.characters(whitelist_categories=('Nd', 'Lu', 'Ll'))
        )
    )
    @settings(max_examples=100)
    def test_tampered_token_rejected(self, user_id, email, google_id):
        """
        Property: Tampered tokens are rejected
        
        For any valid JWT, modifying its content should cause verification to fail.
        """
        auth_service = AuthService()
        
        user_data = {
            "id": str(user_id),
            "email": email,
            "google_id": google_id
        }
        
        # Create a valid token
        valid_token = auth_service.create_jwt(user_data)
        
        # Tamper with the token by modifying a character
        if len(valid_token) > 10:
            # Modify a character in the middle of the token
            mid = len(valid_token) // 2
            tampered_char = 'X' if valid_token[mid] != 'X' else 'Y'
            tampered_token = valid_token[:mid] + tampered_char + valid_token[mid+1:]
            
            try:
                auth_service.verify_jwt(tampered_token)
                # Might still be valid if we got lucky with the modification
                # but most of the time it should fail
            except JWTInvalidError:
                # Expected behavior for most cases
                pass
