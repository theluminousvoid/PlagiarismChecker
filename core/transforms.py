"""
Чистые функции - это функции, которые:
1. Не изменяют входные данные
2. Всегда возвращают одинаковый результат для одинаковых входных данных
3. Не имеют побочных эффектов (не выводят на экран, не записывают в файлы)
"""

import re
import string
from typing import Tuple
from functools import reduce


def normalize(text: str) -> str:
    if not text:
        return ""
    result = text.lower()
    result = result.translate(str.maketrans('', '', string.punctuation))
    result = re.sub(r'\s+', ' ', result).strip()
    return result


def tokenize(text: str) -> Tuple[str, ...]:
    if not text:
        return tuple()
    words = text.split()
    return tuple(filter(lambda word: len(word) > 0, words))


def ngrams(tokens: Tuple[str, ...], n: int = 3) -> Tuple[Tuple[str, ...], ...]:
    if len(tokens) < n:
        return tuple()
    result = []
    for i in range(len(tokens) - n + 1):
        ngram = tuple(tokens[i:i + n])
        result.append(ngram)
    return tuple(result)


def jaccard(a: Tuple[str, ...], b: Tuple[str, ...]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0

    set_a = set(a)
    set_b = set(b)

    intersection_count = reduce(
        lambda count, word: count + (1 if word in set_b else 0),
        set_a,
        0
    )

    union_count = len(set_a | set_b)
    return intersection_count / union_count if union_count > 0 else 0.0
