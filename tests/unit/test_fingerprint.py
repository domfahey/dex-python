"""Tests for fingerprint module - OpenRefine-style keying functions.

These tests are written first (TDD) to define expected behavior.
"""


class TestFingerprint:
    """Test the fingerprint() keying function."""

    def test_basic_fingerprint(self):
        """Basic fingerprint normalizes and sorts tokens."""
        from dex_python.fingerprint import fingerprint

        assert fingerprint("Tom Cruise") == "cruise tom"

    def test_fingerprint_reorders_tokens(self):
        """Fingerprint sorts tokens alphabetically."""
        from dex_python.fingerprint import fingerprint

        assert fingerprint("Cruise, Tom") == "cruise tom"
        assert fingerprint("Tom Cruise") == fingerprint("Cruise, Tom")

    def test_fingerprint_removes_punctuation(self):
        """Fingerprint strips punctuation."""
        from dex_python.fingerprint import fingerprint

        assert fingerprint("O'Brien") == "obrien"
        assert fingerprint("Smith-Jones") == "smithjones"

    def test_fingerprint_normalizes_unicode(self):
        """Fingerprint converts unicode to ASCII."""
        from dex_python.fingerprint import fingerprint

        assert fingerprint("José García") == "garcia jose"
        assert fingerprint("Müller") == "muller"
        assert fingerprint("Björk") == "bjork"

    def test_fingerprint_case_insensitive(self):
        """Fingerprint is case insensitive."""
        from dex_python.fingerprint import fingerprint

        assert fingerprint("TOM CRUISE") == fingerprint("tom cruise")

    def test_fingerprint_deduplicates_tokens(self):
        """Fingerprint removes duplicate tokens."""
        from dex_python.fingerprint import fingerprint

        assert fingerprint("the the cat") == "cat the"

    def test_fingerprint_empty_string(self):
        """Fingerprint handles empty string."""
        from dex_python.fingerprint import fingerprint

        assert fingerprint("") == ""

    def test_fingerprint_none_returns_empty(self):
        """Fingerprint handles None input."""
        from dex_python.fingerprint import fingerprint

        assert fingerprint(None) == ""

    def test_fingerprint_whitespace_only(self):
        """Fingerprint handles whitespace-only input."""
        from dex_python.fingerprint import fingerprint

        assert fingerprint("   ") == ""


class TestNgramFingerprint:
    """Test the ngram_fingerprint() keying function."""

    def test_ngram_1gram(self):
        """1-gram fingerprint returns sorted unique chars."""
        from dex_python.fingerprint import ngram_fingerprint

        # "paris" -> chars: p,a,r,i,s -> sorted: a,i,p,r,s
        assert ngram_fingerprint("paris", n=1) == "aiprs"

    def test_ngram_2gram(self):
        """2-gram fingerprint returns sorted unique 2-grams."""
        from dex_python.fingerprint import ngram_fingerprint

        # "paris" -> 2-grams: pa,ar,ri,is -> sorted: ar,is,pa,ri
        result = ngram_fingerprint("paris", n=2)
        assert result == "arispar" or result == "arispari"  # OpenRefine format

    def test_ngram_removes_whitespace(self):
        """N-gram fingerprint removes whitespace before processing."""
        from dex_python.fingerprint import ngram_fingerprint

        # "New York" -> "newyork" -> n-grams
        assert ngram_fingerprint("New York", n=2) == ngram_fingerprint("newyork", n=2)

    def test_ngram_catches_typos(self):
        """N-gram can match strings with minor differences."""
        from dex_python.fingerprint import ngram_fingerprint

        # These should have very similar 1-gram fingerprints
        fp1 = ngram_fingerprint("Krzysztof", n=1)
        fp2 = ngram_fingerprint("Krzystof", n=1)
        # Both use same letters, just different counts
        assert fp1 == fp2  # Same unique letters

    def test_ngram_empty_string(self):
        """N-gram handles empty string."""
        from dex_python.fingerprint import ngram_fingerprint

        assert ngram_fingerprint("", n=2) == ""

    def test_ngram_none_returns_empty(self):
        """N-gram handles None input."""
        from dex_python.fingerprint import ngram_fingerprint

        assert ngram_fingerprint(None, n=2) == ""


class TestNormalizePhone:
    """Test phone number normalization."""

    def test_strips_dashes(self):
        """Normalize phone removes dashes."""
        from dex_python.fingerprint import normalize_phone

        assert normalize_phone("555-123-4567") == "5551234567"

    def test_strips_parentheses(self):
        """Normalize phone removes parentheses."""
        from dex_python.fingerprint import normalize_phone

        assert normalize_phone("(555) 123-4567") == "5551234567"

    def test_strips_spaces(self):
        """Normalize phone removes spaces."""
        from dex_python.fingerprint import normalize_phone

        assert normalize_phone("555 123 4567") == "5551234567"

    def test_strips_country_code(self):
        """Normalize phone removes +1 country code."""
        from dex_python.fingerprint import normalize_phone

        assert normalize_phone("+1 555-123-4567") == "5551234567"

    def test_strips_dots(self):
        """Normalize phone removes dots."""
        from dex_python.fingerprint import normalize_phone

        assert normalize_phone("555.123.4567") == "5551234567"

    def test_already_normalized(self):
        """Already normalized phone passes through."""
        from dex_python.fingerprint import normalize_phone

        assert normalize_phone("5551234567") == "5551234567"

    def test_empty_string(self):
        """Empty string returns empty."""
        from dex_python.fingerprint import normalize_phone

        assert normalize_phone("") == ""

    def test_none_returns_empty(self):
        """None returns empty string."""
        from dex_python.fingerprint import normalize_phone

        assert normalize_phone(None) == ""


class TestNormalizedLevenshtein:
    """Test normalized Levenshtein distance function."""

    def test_identical_strings(self):
        """Identical strings have distance 0.0."""
        from dex_python.fingerprint import normalized_levenshtein

        assert normalized_levenshtein("hello", "hello") == 0.0

    def test_completely_different(self):
        """Completely different strings have distance 1.0."""
        from dex_python.fingerprint import normalized_levenshtein

        assert normalized_levenshtein("abc", "xyz") == 1.0

    def test_one_char_difference(self):
        """One char difference normalized by length."""
        from dex_python.fingerprint import normalized_levenshtein

        # "cat" vs "bat" = 1 edit, max length 3 -> 1/3 = 0.333...
        result = normalized_levenshtein("cat", "bat")
        assert 0.3 < result < 0.4

    def test_empty_vs_nonempty(self):
        """Empty vs non-empty has distance 1.0."""
        from dex_python.fingerprint import normalized_levenshtein

        assert normalized_levenshtein("", "hello") == 1.0
        assert normalized_levenshtein("hello", "") == 1.0

    def test_both_empty(self):
        """Both empty strings have distance 0.0."""
        from dex_python.fingerprint import normalized_levenshtein

        assert normalized_levenshtein("", "") == 0.0


class TestEnsembleSimilarity:
    """Test weighted ensemble similarity scoring."""

    def test_identical_strings(self):
        """Identical strings have similarity 1.0."""
        from dex_python.fingerprint import ensemble_similarity

        assert ensemble_similarity("hello", "hello") == 1.0

    def test_similar_strings(self):
        """Similar strings have high similarity."""
        from dex_python.fingerprint import ensemble_similarity

        # Jonathan vs Jonathon - very similar
        score = ensemble_similarity("Jonathan", "Jonathon")
        assert score > 0.85

    def test_different_strings(self):
        """Different strings have low similarity."""
        from dex_python.fingerprint import ensemble_similarity

        score = ensemble_similarity("Alice", "Zebra")
        assert score < 0.5

    def test_custom_weights(self):
        """Custom weights are applied correctly."""
        from dex_python.fingerprint import ensemble_similarity

        # With 100% Jaro-Winkler weight
        score_jw = ensemble_similarity("test", "tset", jw_weight=1.0, lev_weight=0.0)
        # With 100% Levenshtein weight
        score_lev = ensemble_similarity("test", "tset", jw_weight=0.0, lev_weight=1.0)
        # These should be different
        assert score_jw != score_lev
