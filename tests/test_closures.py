import pytest
from core.closures import (
    by_author,
    by_title,
    by_min_length,
    by_date_range,
    compose_filters,
    create_similarity_threshold
)

# Mock Document
class Document:
    def __init__(self, author, title, text, ts):
        self.author = author
        self.title = title
        self.text = text
        self.ts = ts

# 1. Тест by_author
def test_by_author():
    doc1 = Document("Knuth", "Algo", "text", "2025-01-01")
    doc2 = Document("Turing", "AI", "text", "2025-01-01")
    filter_knuth = by_author("Knuth")
    assert filter_knuth(doc1) is True
    assert filter_knuth(doc2) is False

# 2. Тест by_title
def test_by_title():
    doc = Document("Alice", "Introduction to Algorithms", "text", "2025-01-01")
    filter_algo = by_title("algorithm")
    assert filter_algo(doc) is True
    assert by_title("data")(doc) is False

# 3. Тест by_min_length
def test_by_min_length():
    doc_short = Document("A", "T", "123", "2025-01-01")
    doc_long = Document("B", "T", "123456", "2025-01-01")
    filter_len = by_min_length(5)
    assert filter_len(doc_short) is False
    assert filter_len(doc_long) is True

# 4. Тест by_date_range
def test_by_date_range():
    doc = Document("A", "T", "text", "2025-06-15")
    filter_range = by_date_range("2025-01-01", "2025-12-31")
    assert filter_range(doc) is True
    filter_range2 = by_date_range("2026-01-01", "2026-12-31")
    assert filter_range2(doc) is False

# 5. Тест compose_filters и create_similarity_threshold
def test_compose_filters_and_threshold():
    doc = Document("Knuth", "Algorithms", "123456", "2025-06-01")
    combined = compose_filters(
        by_author("Knuth"),
        by_title("algo"),
        by_min_length(5),
        by_date_range("2025-01-01", "2025-12-31")
    )
    assert combined(doc) is True
    # similarity threshold
    threshold_checker = create_similarity_threshold(0.7)
    assert threshold_checker(0.8) is True
    assert threshold_checker(0.6) is False
