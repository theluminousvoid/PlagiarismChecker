import sys, os
# пусть тесты всегда запускаются из корня репо и видят пакет core
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.transforms import normalize, tokenize, ngrams, jaccard


def test_normalize_basic():
    assert normalize("Hello, World!  ") == "hello world"


def test_tokenize_empty():
    assert tokenize("") == ()


def test_tokenize_words():
    assert tokenize("a   b c") == ("a", "b", "c")


def test_ngrams_trigrams():
    toks = ("a", "b", "c", "d")
    assert ngrams(toks, 3) == (("a", "b", "c"), ("b", "c", "d"))


def test_jaccard_similarity_range():
    a = ("a", "b", "c")
    b = ("b", "c", "d")
    s = jaccard(a, b)
    assert 0 < s < 1
