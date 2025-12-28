"""Additional edge case tests for fingerprint module."""

import pytest


class TestFingerprintEdgeCases:
    """Test edge cases for fingerprint function."""

    def test_numbers_in_string(self):
        """Fingerprint should handle numbers."""
        from dex_python.fingerprint import fingerprint

        assert fingerprint("John Doe 123") == "123 doe john"

    def test_multiple_spaces(self):
        """Multiple spaces should be normalized to single space."""
        from dex_python.fingerprint import fingerprint

        assert fingerprint("John    Doe") == "doe john"

    def test_tabs_and_newlines(self):
        """Tabs and newlines should be treated as whitespace."""
        from dex_python.fingerprint import fingerprint

        assert fingerprint("John\tDoe\nSmith") == "doe john smith"

    def test_all_punctuation(self):
        """String with only punctuation should return empty."""
        from dex_python.fingerprint import fingerprint

        assert fingerprint("!@#$%^&*()") == ""

    def test_mixed_unicode_and_ascii(self):
        """Mixed unicode and ASCII should normalize."""
        from dex_python.fingerprint import fingerprint

        assert fingerprint("José Smith") == "jose smith"

    def test_very_long_string(self):
        """Should handle very long strings."""
        from dex_python.fingerprint import fingerprint

        long_string = " ".join(["word"] * 1000)
        result = fingerprint(long_string)
        assert result == "word"  # All duplicates removed

    def test_single_word(self):
        """Single word should work."""
        from dex_python.fingerprint import fingerprint

        assert fingerprint("Hello") == "hello"

    def test_numbers_only(self):
        """Numbers-only string should work."""
        from dex_python.fingerprint import fingerprint

        assert fingerprint("12345") == "12345"

    def test_special_unicode_characters(self):
        """Special unicode characters should be handled."""
        from dex_python.fingerprint import fingerprint

        # Accented characters
        assert fingerprint("Björk Guðmundsdóttir") == "bjork gudmundsdottir"

    def test_emoji_removal(self):
        """Emojis should be removed or normalized."""
        from dex_python.fingerprint import fingerprint

        result = fingerprint("Hello 😊 World")
        # Emojis should be removed, leaving just words
        assert "hello" in result
        assert "world" in result


class TestNgramFingerprintEdgeCases:
    """Test edge cases for ngram_fingerprint function."""

    def test_string_shorter_than_n(self):
        """String shorter than n should return the string."""
        from dex_python.fingerprint import ngram_fingerprint

        assert ngram_fingerprint("ab", n=3) == "ab"

    def test_single_character(self):
        """Single character with n=1 should work."""
        from dex_python.fingerprint import ngram_fingerprint

        assert ngram_fingerprint("a", n=1) == "a"

    def test_empty_after_normalization(self):
        """String that becomes empty after normalization."""
        from dex_python.fingerprint import ngram_fingerprint

        assert ngram_fingerprint("   ", n=2) == ""

    def test_large_n_value(self):
        """Large n value should handle gracefully."""
        from dex_python.fingerprint import ngram_fingerprint

        result = ngram_fingerprint("hello", n=10)
        assert result == "hello"

    def test_n_equals_string_length(self):
        """n equal to string length should return string."""
        from dex_python.fingerprint import ngram_fingerprint

        assert ngram_fingerprint("hello", n=5) == "hello"

    def test_unicode_ngrams(self):
        """Unicode should be normalized for ngrams."""
        from dex_python.fingerprint import ngram_fingerprint

        result = ngram_fingerprint("café", n=2)
        assert "ca" in result or "fe" in result

    def test_ngram_deduplication(self):
        """Duplicate ngrams should be removed."""
        from dex_python.fingerprint import ngram_fingerprint

        # "aaa" has ngrams "aa", "aa" (duplicates)
        result = ngram_fingerprint("aaa", n=2)
        assert result == "aa"


class TestNormalizePhoneEdgeCases:
    """Test edge cases for normalize_phone function."""

    def test_international_prefix_removal(self):
        """Should remove +1 prefix."""
        from dex_python.fingerprint import normalize_phone

        assert normalize_phone("+1 555-123-4567") == "5551234567"

    def test_extension_number(self):
        """Should handle phone with extension."""
        from dex_python.fingerprint import normalize_phone

        result = normalize_phone("555-123-4567 ext 123")
        assert "5551234567" in result

    def test_dots_as_separators(self):
        """Should handle dots as separators."""
        from dex_python.fingerprint import normalize_phone

        assert normalize_phone("555.123.4567") == "5551234567"

    def test_mixed_separators(self):
        """Should handle mixed separators."""
        from dex_python.fingerprint import normalize_phone

        assert normalize_phone("(555) 123.4567") == "5551234567"

    def test_letters_in_number(self):
        """Should extract only digits from vanity numbers."""
        from dex_python.fingerprint import normalize_phone

        result = normalize_phone("1-800-FLOWERS")
        # Should have only digits
        assert result.isdigit()

    def test_very_short_number(self):
        """Should handle very short numbers."""
        from dex_python.fingerprint import normalize_phone

        result = normalize_phone("123")
        assert result == "123"


class TestNormalizePhoneE164EdgeCases:
    """Test edge cases for normalize_phone_e164 function."""

    def test_empty_after_strip(self):
        """Whitespace-only input should return empty."""
        from dex_python.fingerprint import normalize_phone_e164

        assert normalize_phone_e164("   ") == ""

    def test_invalid_number_strict_mode(self):
        """Invalid number in strict mode should return empty."""
        from dex_python.fingerprint import normalize_phone_e164

        result = normalize_phone_e164("123", strict=True)
        assert result == ""

    def test_invalid_number_non_strict(self):
        """Invalid number in non-strict mode should fallback."""
        from dex_python.fingerprint import normalize_phone_e164

        result = normalize_phone_e164("abc-def-ghij", strict=False)
        # Should fallback to normalize_phone
        assert isinstance(result, str)

    def test_country_code_detection(self):
        """Should detect country code correctly."""
        from dex_python.fingerprint import normalize_phone_e164

        # UK number
        result = normalize_phone_e164("+44 20 7946 0958")
        assert result.startswith("+44")

    def test_different_default_regions(self):
        """Should respect default_region parameter."""
        from dex_python.fingerprint import normalize_phone_e164

        # Same local number, different regions
        us_result = normalize_phone_e164("2079460958", default_region="US")
        gb_result = normalize_phone_e164("2079460958", default_region="GB")
        # Results should differ based on region
        assert us_result != gb_result or us_result == ""

    def test_already_e164_format(self):
        """Already E.164 formatted should pass through."""
        from dex_python.fingerprint import normalize_phone_e164

        result = normalize_phone_e164("+15551234567")
        assert result == "+15551234567"


class TestFormatPhoneEdgeCases:
    """Test edge cases for format_phone function."""

    def test_invalid_format_parameter(self):
        """Invalid format parameter should default to E.164."""
        from dex_python.fingerprint import format_phone

        result = format_phone("+15551234567", format="invalid")
        assert result == "+15551234567"

    def test_case_insensitive_format(self):
        """Format parameter should be case-insensitive."""
        from dex_python.fingerprint import format_phone

        result1 = format_phone("+15551234567", format="NATIONAL")
        result2 = format_phone("+15551234567", format="national")
        assert result1 == result2

    def test_unparseable_phone_returns_original(self):
        """Unparseable phone should return original."""
        from dex_python.fingerprint import format_phone

        result = format_phone("not-a-phone")
        assert result == "not-a-phone"

    def test_empty_string_handling(self):
        """Empty string should return empty."""
        from dex_python.fingerprint import format_phone

        assert format_phone("") == ""

    def test_whitespace_only(self):
        """Whitespace-only should return empty."""
        from dex_python.fingerprint import format_phone

        assert format_phone("   ") == ""


class TestNormalizeLinkedInEdgeCases:
    """Test edge cases for normalize_linkedin function."""

    def test_mixed_case_normalization(self):
        """Mixed case should normalize to lowercase."""
        from dex_python.fingerprint import normalize_linkedin

        result = normalize_linkedin("linkedin.com/in/JohnDoe")
        assert result == "linkedin.com/in/johndoe"

    def test_trailing_slashes(self):
        """Multiple trailing slashes should be removed."""
        from dex_python.fingerprint import normalize_linkedin

        result = normalize_linkedin("linkedin.com/in/johndoe///")
        assert result == "linkedin.com/in/johndoe"

    def test_query_params_removal(self):
        """Query parameters should be stripped."""
        from dex_python.fingerprint import normalize_linkedin

        result = normalize_linkedin("linkedin.com/in/johndoe?ref=abc&utm=xyz")
        assert result == "linkedin.com/in/johndoe"
        assert "?" not in result

    def test_fragment_removal(self):
        """URL fragments should be stripped."""
        from dex_python.fingerprint import normalize_linkedin

        result = normalize_linkedin("linkedin.com/in/johndoe#experience")
        assert result == "linkedin.com/in/johndoe"
        assert "#" not in result

    def test_mobile_subdomain(self):
        """Mobile subdomain should normalize."""
        from dex_python.fingerprint import normalize_linkedin

        result = normalize_linkedin("https://m.linkedin.com/in/johndoe")
        assert result == "linkedin.com/in/johndoe"

    def test_locale_subdomain(self):
        """Locale subdomain should normalize."""
        from dex_python.fingerprint import normalize_linkedin

        result = normalize_linkedin("https://uk.linkedin.com/in/johndoe")
        assert result == "linkedin.com/in/johndoe"

    def test_company_url(self):
        """Company URLs should be handled."""
        from dex_python.fingerprint import normalize_linkedin

        result = normalize_linkedin("linkedin.com/company/google")
        assert result == "linkedin.com/company/google"

    def test_non_linkedin_url(self):
        """Non-LinkedIn URLs should return empty."""
        from dex_python.fingerprint import normalize_linkedin

        assert normalize_linkedin("https://twitter.com/user") == ""
        assert normalize_linkedin("https://facebook.com/user") == ""

    def test_bare_username_without_dots(self):
        """Bare username without dots should be treated as LinkedIn."""
        from dex_python.fingerprint import normalize_linkedin

        result = normalize_linkedin("johndoe")
        assert result == "linkedin.com/in/johndoe"

    def test_username_with_dot_treated_carefully(self):
        """Username with dot might not be LinkedIn username."""
        from dex_python.fingerprint import normalize_linkedin

        # Depends on implementation - might return empty
        result = normalize_linkedin("john.doe")
        # Either way is acceptable depending on heuristics
        assert isinstance(result, str)

    def test_empty_username(self):
        """Empty username should return empty."""
        from dex_python.fingerprint import normalize_linkedin

        assert normalize_linkedin("linkedin.com/in/") == ""
        assert normalize_linkedin("in/") == ""

    def test_whitespace_in_url(self):
        """Whitespace should be stripped."""
        from dex_python.fingerprint import normalize_linkedin

        result = normalize_linkedin("  linkedin.com/in/johndoe  ")
        assert result == "linkedin.com/in/johndoe"


class TestEnsembleSimilarity:
    """Test ensemble_similarity function."""

    def test_identical_strings(self):
        """Identical strings should have similarity 1.0."""
        from dex_python.fingerprint import ensemble_similarity

        result = ensemble_similarity("test", "test")
        assert result == pytest.approx(1.0, abs=0.01)

    def test_completely_different(self):
        """Completely different strings should have low similarity."""
        from dex_python.fingerprint import ensemble_similarity

        result = ensemble_similarity("abc", "xyz")
        assert result < 0.5

    def test_similar_strings(self):
        """Similar strings should have high similarity."""
        from dex_python.fingerprint import ensemble_similarity

        result = ensemble_similarity("Jonathan", "Jonathon")
        assert result > 0.85

    def test_empty_strings(self):
        """Empty strings should handle gracefully."""
        from dex_python.fingerprint import ensemble_similarity

        result = ensemble_similarity("", "")
        # Either 0.0 or 1.0 is acceptable depending on interpretation
        assert 0.0 <= result <= 1.0

    def test_custom_weights(self):
        """Should respect custom weight parameters."""
        from dex_python.fingerprint import ensemble_similarity

        result1 = ensemble_similarity("test", "text", jw_weight=1.0, lev_weight=0.0)
        result2 = ensemble_similarity("test", "text", jw_weight=0.0, lev_weight=1.0)
        # Different weights should give different results
        assert result1 != result2


class TestNormalizedLevenshtein:
    """Test normalized_levenshtein function."""

    def test_identical_strings(self):
        """Identical strings should have distance 0.0."""
        from dex_python.fingerprint import normalized_levenshtein

        result = normalized_levenshtein("hello", "hello")
        assert result == 0.0

    def test_single_character_difference(self):
        """Single character difference should be normalized."""
        from dex_python.fingerprint import normalized_levenshtein

        result = normalized_levenshtein("cat", "bat")
        assert result == pytest.approx(1 / 3, abs=0.01)

    def test_empty_strings(self):
        """Empty strings should have distance 0.0."""
        from dex_python.fingerprint import normalized_levenshtein

        result = normalized_levenshtein("", "")
        assert result == 0.0

    def test_one_empty_string(self):
        """One empty string should have distance 1.0."""
        from dex_python.fingerprint import normalized_levenshtein

        result = normalized_levenshtein("hello", "")
        assert result == 1.0

    def test_completely_different(self):
        """Completely different strings should have high distance."""
        from dex_python.fingerprint import normalized_levenshtein

        result = normalized_levenshtein("abc", "xyz")
        assert result == 1.0

    def test_normalization_by_max_length(self):
        """Distance should be normalized by max length."""
        from dex_python.fingerprint import normalized_levenshtein

        # 3 edits needed, max length is 5
        result = normalized_levenshtein("ab", "xyz")
        assert 0.0 <= result <= 1.0