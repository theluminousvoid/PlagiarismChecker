import pytest
from core.transforms import normalize, tokenize, ngrams, jaccard

# 1. Тест normalize
def test_normalize():
    assert normalize(" Hello, World! ") == "hello world"
    assert normalize("Multiple   spaces") == "multiple spaces"
    assert normalize("") == ""
    assert normalize(None) == ""  # Проверка на None
    assert normalize("Punctuation!!!") == "punctuation"

# 2. Тест tokenize
def test_tokenize():
    assert tokenize("hello world") == ("hello", "world")
    assert tokenize("   multiple   spaces ") == ("multiple", "spaces")
    assert tokenize("") == ()
    assert tokenize(None) == ()
    assert tokenize("word,, word!!") == ("word,,", "word!!")  # tokenize не удаляет пунктуацию

# 3. Тест ngrams
def test_ngrams():
    tokens = ("a", "b", "c", "d")
    assert ngrams(tokens, 2) == (("a","b"), ("b","c"), ("c","d"))
    assert ngrams(tokens, 3) == (("a","b","c"), ("b","c","d"))
    assert ngrams(tokens, 5) == ()
    assert ngrams((), 2) == ()

# 4. Тест jaccard
def test_jaccard_basic():
    a = ("a", "b", "c")
    b = ("b", "c", "d")
    c = ("x", "y")
    assert jaccard(a, b) == 2/4  # 2 общих / 4 уникальных
    assert jaccard(a, c) == 0.0
    assert jaccard((), ()) == 1.0
    assert jaccard(a, ()) == 0.0

# 5. Комбинированный тест: normalize + tokenize + ngrams
def test_pipeline():
    text = "Hello, world! This is a test."
    norm = normalize(text)
    tokens = tokenize(norm)
    grams = ngrams(tokens, 2)
    assert norm == "hello world this is a test"
    assert tokens == ("hello", "world", "this", "is", "a", "test")
    assert grams == (("hello","world"), ("world","this"), ("this","is"), ("is","a"), ("a","test"))
