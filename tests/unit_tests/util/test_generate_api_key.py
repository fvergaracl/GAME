import hashlib
import string
import unittest

from app.util.generate_api_key import (DEFAULT_KEY_NAMESPACE,
                                       PREFIX_RANDOM_LEN,
                                       SECRET_RANDOM_LEN,
                                       extract_prefix, generate_api_key,
                                       hash_api_key)


class TestGenerateApiKey(unittest.TestCase):

    def test_generated_key_shape_carries_namespace_prefix_and_dot(self):
        """The plaintext is namespaced and split by a dot separator."""
        generated = generate_api_key()
        self.assertTrue(generated.plaintext.startswith(DEFAULT_KEY_NAMESPACE))
        self.assertIn(".", generated.plaintext)
        prefix, secret = generated.plaintext.split(".", 1)
        self.assertEqual(prefix, generated.prefix)
        self.assertEqual(len(secret), SECRET_RANDOM_LEN)

    def test_prefix_has_expected_length(self):
        """The prefix is `<namespace><PREFIX_RANDOM_LEN chars>`."""
        generated = generate_api_key()
        expected_len = len(DEFAULT_KEY_NAMESPACE) + PREFIX_RANDOM_LEN
        self.assertEqual(len(generated.prefix), expected_len)

    def test_hash_matches_sha256_of_plaintext(self):
        """The reported hash is sha256 of the plaintext."""
        generated = generate_api_key()
        expected = hashlib.sha256(
            generated.plaintext.encode("utf-8")
        ).hexdigest()
        self.assertEqual(generated.key_hash, expected)

    def test_two_invocations_yield_distinct_plaintext_and_hash(self):
        """Successive calls draw fresh entropy, not repeated values."""
        first = generate_api_key()
        second = generate_api_key()
        self.assertNotEqual(first.plaintext, second.plaintext)
        self.assertNotEqual(first.key_hash, second.key_hash)
        self.assertNotEqual(first.prefix, second.prefix)

    def test_plaintext_only_contains_urlsafe_characters(self):
        """No spaces or non-urlsafe characters leak into the plaintext."""
        generated = generate_api_key()
        allowed = set(string.ascii_letters + string.digits + "_-.")
        self.assertTrue(set(generated.plaintext).issubset(allowed))

    def test_hash_api_key_is_deterministic(self):
        """`hash_api_key` produces a stable sha256 hex digest."""
        plaintext = "gme_live_aaaaaaaa.bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        first = hash_api_key(plaintext)
        second = hash_api_key(plaintext)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_extract_prefix_returns_part_before_dot(self):
        """New-format keys: prefix is the portion before the first dot."""
        plaintext = "gme_live_abcdefgh.0123456789abcdef0123456789abcdef"
        self.assertEqual(extract_prefix(plaintext), "gme_live_abcdefgh")

    def test_extract_prefix_falls_back_to_legacy_namespace(self):
        """Legacy plaintexts without a dot map to a deterministic prefix."""
        legacy_value = "legacy-plaintext-key-without-dot"
        extracted = extract_prefix(legacy_value)
        self.assertTrue(extracted.startswith("gme_legacy_"))
        # Deterministic: depends only on hash of the plaintext.
        digest = hashlib.sha256(
            legacy_value.encode("utf-8")
        ).hexdigest()[:12]
        self.assertEqual(extracted, f"gme_legacy_{digest}")


if __name__ == "__main__":
    unittest.main()
