import pytest
from core.recursion import (
    flatten_nested_tuples,
    sum_tuple_recursive,
    count_documents_by_author_recursive,
    compare_submissions_recursive,
    tree_walk_documents
)

# Mock классы и функции
class Document:
    def __init__(self, id, text, author=""):
        self.id = id
        self.text = text
        self.author = author

class Submission:
    def __init__(self, id, text):
        self.id = id
        self.text = text

# Подменяем jaccard и text_processing_pipeline для тестов
import core.recursion

core.recursion.jaccard = lambda a, b: 1.0 if a == b else 0.5
core.recursion._text_to_ngrams = lambda text, n=3: tuple(text.split())

# 1. Тест flatten_nested_tuples
def test_flatten_nested_tuples():
    nested = ((1, 2), 3, (4, (5, 6)))
    flat = flatten_nested_tuples(nested)
    assert flat == (1, 2, 3, 4, 5, 6)

# 2. Тест sum_tuple_recursive
def test_sum_tuple_recursive():
    values = (1.0, 2.0, 3.0, 4.0)
    assert sum_tuple_recursive(values) == 10.0
    assert sum_tuple_recursive(()) == 0.0
    assert sum_tuple_recursive((42,)) == 42.0

# 3. Тест count_documents_by_author_recursive
def test_count_documents_by_author_recursive():
    docs = (
        Document("1", "text1", "Alice"),
        Document("2", "text2", "Bob"),
        Document("3", "text3", "alice"),
    )
    assert count_documents_by_author_recursive(docs, "alice") == 2
    assert count_documents_by_author_recursive(docs, "Bob") == 1
    assert count_documents_by_author_recursive(docs, "Charlie") == 0

# 4. Тест compare_submissions_recursive
def test_compare_submissions_recursive():
    subs = (Submission("s1", "a b c"), Submission("s2", "d e"))
    docs = (Document("d1", "a b c"), Document("d2", "x y z"))
    results = compare_submissions_recursive(subs, docs)
    assert isinstance(results, tuple)
    assert all(isinstance(r, float) for r in results)
    # проверка на равенство с ожидаемым jaccard через нашу подмену
    assert results == (1.0, 0.5)

# 5. Тест tree_walk_documents
def test_tree_walk_documents():
    docs = (
        Document("1", "a b c"),
        Document("2", "a b c"),
        Document("3", "x y z")
    )
    path = tree_walk_documents(docs, root=0, max_depth=2)
    assert isinstance(path, tuple)
    assert "1" in path
    assert len(path) <= 2  # max_depth ограничивает
