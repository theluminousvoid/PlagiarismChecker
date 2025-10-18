"""
Композиция функций и пайплайны.
Функциональные паттерны
"""
from typing import Callable, Tuple
from functools import reduce
from core.transforms import normalize, tokenize, ngrams


def pipe(*functions: Callable) -> Callable:
    """
    Композиция функций слева направо: pipe(f, g, h)(x) = h(g(f(x)))
    """
    def piped(x):
        return reduce(lambda acc, f: f(acc), functions, x)
    return piped


def text_processing_pipeline(text: str, n: int = 3) -> Tuple:
    """
    Полный пайплайн обработки текста.
    Возвращает (normalized, tokens, ngrams)
    """
    normalized = normalize(text)
    tokens = tokenize(normalized)
    grams = ngrams(tokens, n)
    return (normalized, tokens, grams)
