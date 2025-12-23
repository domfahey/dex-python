"""OpenRefine-style fingerprinting and normalization utilities.

This module provides keying functions for deduplication based on
OpenRefine's clustering algorithms.

Example:
    >>> from dex_python.fingerprint import fingerprint, ngram_fingerprint
    >>> fingerprint("Tom Cruise")
    'cruise tom'
    >>> fingerprint("Cruise, Tom")
    'cruise tom'
    >>> ngram_fingerprint("paris", n=1)
    'aiprs'
"""

import re
import string

import jellyfish
from unidecode import unidecode


def fingerprint(value: str | None) -> str:
    """Create OpenRefine-style fingerprint for clustering.

    Performs these operations in order:
    1. Strip leading/trailing whitespace
    2. Convert to lowercase
    3. Normalize unicode to ASCII
    4. Remove punctuation and control characters
    5. Split into whitespace-separated tokens
    6. Sort tokens alphabetically
    7. Remove duplicate tokens
    8. Rejoin with single space

    Args:
        value: String to fingerprint.

    Returns:
        Fingerprint string, or empty string if input is None/empty.

    Example:
        >>> fingerprint("José García")
        'garcia jose'
        >>> fingerprint("Tom Cruise") == fingerprint("Cruise, Tom")
        True
    """
    if value is None:
        return ""

    # Strip and lowercase
    value = value.strip().lower()
    if not value:
        return ""

    # Normalize unicode to ASCII (José -> Jose)
    value = unidecode(value)

    # Remove punctuation
    value = value.translate(str.maketrans("", "", string.punctuation))

    # Split into tokens, sort, dedupe, rejoin
    tokens = value.split()
    unique_tokens = list(dict.fromkeys(tokens))  # Preserve first occurrence, dedupe
    unique_tokens.sort()

    return " ".join(unique_tokens)


def ngram_fingerprint(value: str | None, n: int = 2) -> str:
    """Create n-gram fingerprint for fuzzy matching.

    Performs these operations:
    1. Convert to lowercase
    2. Remove all whitespace
    3. Normalize unicode to ASCII
    4. Remove punctuation
    5. Extract all n-character substrings
    6. Sort n-grams alphabetically
    7. Remove duplicates
    8. Concatenate

    Args:
        value: String to fingerprint.
        n: Size of n-grams (default: 2).

    Returns:
        N-gram fingerprint string, or empty string if input is None/empty.

    Example:
        >>> ngram_fingerprint("paris", n=1)
        'aiprs'
    """
    if value is None:
        return ""

    # Lowercase and remove whitespace
    value = value.lower().replace(" ", "")
    if not value:
        return ""

    # Normalize unicode and remove punctuation
    value = unidecode(value)
    value = value.translate(str.maketrans("", "", string.punctuation))

    if len(value) < n:
        return value

    # Extract n-grams
    ngrams = [value[i : i + n] for i in range(len(value) - n + 1)]

    # Sort and dedupe
    unique_ngrams = sorted(set(ngrams))

    return "".join(unique_ngrams)


def normalize_phone(phone: str | None) -> str:
    """Normalize phone number by extracting digits only.

    Removes all formatting characters including:
    - Dashes, parentheses, spaces, dots
    - Country code prefix (+1)

    Args:
        phone: Phone number string.

    Returns:
        Digits-only phone number, or empty string if input is None/empty.

    Example:
        >>> normalize_phone("(555) 123-4567")
        '5551234567'
        >>> normalize_phone("+1 555-123-4567")
        '5551234567'
    """
    if phone is None:
        return ""

    # Remove +1 country code prefix
    phone = re.sub(r"^\+1\s*", "", phone)

    # Extract digits only
    digits = re.sub(r"\D", "", phone)

    return digits


def normalized_levenshtein(s1: str, s2: str) -> float:
    """Calculate normalized Levenshtein distance between two strings.

    Returns a value between 0.0 (identical) and 1.0 (completely different).
    Normalization is by the maximum string length.

    Args:
        s1: First string.
        s2: Second string.

    Returns:
        Normalized distance from 0.0 to 1.0.

    Example:
        >>> normalized_levenshtein("cat", "bat")
        0.333...
        >>> normalized_levenshtein("hello", "hello")
        0.0
    """
    if not s1 and not s2:
        return 0.0

    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 0.0

    distance = jellyfish.levenshtein_distance(s1, s2)
    return distance / max_len


def ensemble_similarity(
    s1: str,
    s2: str,
    jw_weight: float = 0.6,
    lev_weight: float = 0.4,
) -> float:
    """Calculate weighted ensemble similarity score.

    Combines Jaro-Winkler similarity with normalized Levenshtein
    similarity for more robust matching.

    Args:
        s1: First string.
        s2: Second string.
        jw_weight: Weight for Jaro-Winkler score (default: 0.6).
        lev_weight: Weight for Levenshtein score (default: 0.4).

    Returns:
        Combined similarity score from 0.0 to 1.0.

    Example:
        >>> ensemble_similarity("Jonathan", "Jonathon")
        0.95...
    """
    # Jaro-Winkler returns similarity (0-1)
    jw_score = jellyfish.jaro_winkler_similarity(s1, s2)

    # Convert Levenshtein distance to similarity
    lev_distance = normalized_levenshtein(s1, s2)
    lev_score = 1.0 - lev_distance

    # Weighted combination
    return (jw_weight * jw_score) + (lev_weight * lev_score)
