"""Unit tests for APIKey model."""

import pytest

from app.models import APIKey


class TestAPIKeyHashing:
    """Tests for API key hashing functionality."""

    def test_hash_key_returns_64_char_hex(self):
        """SHA-256 hash should return 64 character hex string."""
        result = APIKey.hash_key("test-key")

        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_hash_key_is_deterministic(self):
        """Same input should always produce same hash."""
        key = "my-secret-key"

        hash1 = APIKey.hash_key(key)
        hash2 = APIKey.hash_key(key)

        assert hash1 == hash2

    def test_hash_key_different_inputs_produce_different_hashes(self):
        """Different keys should produce different hashes."""
        hash1 = APIKey.hash_key("key-one")
        hash2 = APIKey.hash_key("key-two")

        assert hash1 != hash2

    def test_hash_key_is_case_sensitive(self):
        """Hashing should be case-sensitive."""
        hash_lower = APIKey.hash_key("mykey")
        hash_upper = APIKey.hash_key("MYKEY")

        assert hash_lower != hash_upper


class TestAPIKeyGeneration:
    """Tests for API key generation functionality."""

    def test_generate_key_returns_tuple_of_three(self):
        """Generate should return (plain_key, hash, prefix)."""
        result = APIKey.generate_key()

        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_generate_key_plain_key_starts_with_prefix(self):
        """Generated key should start with 'map_' prefix."""
        plain_key, _, _ = APIKey.generate_key()

        assert plain_key.startswith("map_")

    def test_generate_key_hash_matches_plain_key(self):
        """Returned hash should match hash of plain key."""
        plain_key, key_hash, _ = APIKey.generate_key()

        expected_hash = APIKey.hash_key(plain_key)

        assert key_hash == expected_hash

    def test_generate_key_prefix_is_first_12_chars(self):
        """Prefix should be first 12 characters of plain key."""
        plain_key, _, key_prefix = APIKey.generate_key()

        assert key_prefix == plain_key[:12]

    def test_generate_key_produces_unique_keys(self):
        """Each call should produce a unique key."""
        keys = [APIKey.generate_key()[0] for _ in range(10)]

        assert len(set(keys)) == 10

    def test_generate_key_sufficient_length(self):
        """Generated key should have sufficient entropy (32+ chars)."""
        plain_key, _, _ = APIKey.generate_key()

        # map_ (4) + 32 hex chars = 36 total
        assert len(plain_key) >= 32
