import pytest
from core.compose import pipe, text_processing_pipeline
from core.transforms import normalize, tokenize, ngrams

# --------------------------
# Тесты для pipe
# --------------------------

def test_pipe_simple_functions():
    def add1(x): return x + 1
    def times2(x): return x * 2
    p = pipe(add1, times2)
    assert p(3) == 8  # (3+1)*2 = 8

def test_pipe_no_functions_returns_input():
    p = pipe()
    assert p(42) == 42
    assert p("text") == "text"

def test_pipe_multiple_functions_order():
    def f(x): return x + "a"
    def g(x): return x + "b"
    def h(x): return x + "c"
    p = pipe(f, g, h)
    assert p("x") == "xabc"  # f -> g -> h

# --------------------------
# Тесты для text_processing_pipeline
# --------------------------

def test_text_processing_pipeline_structure(monkeypatch):
    # Подменим функции normalize, tokenize, ngrams для контроля
    monkeypatch.setattr("core.compose.normalize", lambda x: x.lower())
    monkeypatch.setattr("core.compose.tokenize", lambda x: x.split())
    monkeypatch.setattr("core.compose.ngrams", lambda tokens, n: [tokens[i:i+n] for i in range(len(tokens)-n+1)])

    text = "Hello World"
    normalized, tokens, grams = text_processing_pipeline(text, n=2)

    assert normalized == "hello world"
    assert tokens == ["hello", "world"]
    assert grams == [["hello", "world"]]

def test_text_processing_pipeline_default_n(monkeypatch):
    monkeypatch.setattr("core.compose.normalize", lambda x: x)
    monkeypatch.setattr("core.compose.tokenize", lambda x: x.split())
    monkeypatch.setattr("core.compose.ngrams", lambda tokens, n: [tokens[i:i+n] for i in range(len(tokens)-n+1)])

    text = "one two three"
    _, tokens, grams = text_processing_pipeline(text)
    assert grams == [["one", "two", "three"]]  # n=3 по умолчанию
