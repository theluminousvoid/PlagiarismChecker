import pytest
from core.ftypes import Maybe, Either, safe_get_document, validate_submission, validate_ngram_size
from core.domain import Document

# --------------------------
# Тесты для Maybe
# --------------------------

def test_maybe_just_and_nothing():
    maybe_val = Maybe.just(42)
    assert maybe_val.is_just()
    assert not maybe_val.is_nothing()
    assert maybe_val.get() == 42

    maybe_empty = Maybe.nothing()
    assert maybe_empty.is_nothing()
    assert not maybe_empty.is_just()
    assert maybe_empty.get(0) == 0

def test_maybe_map_and_flat_map():
    maybe_val = Maybe.just(5)
    mapped = maybe_val.map(lambda x: x * 2)
    assert mapped.get() == 10

    # flat_map возвращает Maybe
    flat_mapped = maybe_val.flat_map(lambda x: Maybe.just(x + 3))
    assert flat_mapped.get() == 8

    # map на nothing
    assert Maybe.nothing().map(lambda x: x*2).is_nothing()
    assert Maybe.nothing().flat_map(lambda x: Maybe.just(x*2)).is_nothing()

def test_maybe_filter_and_or_else():
    maybe_val = Maybe.just(10)
    filtered = maybe_val.filter(lambda x: x > 5)
    assert filtered.is_just()

    filtered_empty = maybe_val.filter(lambda x: x < 5)
    assert filtered_empty.is_nothing()

    assert maybe_val.or_else(0) == 10
    assert Maybe.nothing().or_else(99) == 99

# --------------------------
# Тесты для Either
# --------------------------

def test_either_right_and_left():
    right_val = Either.right(100)
    assert right_val.is_right()
    assert not right_val.is_left()
    assert right_val.get_right() == 100
    assert right_val.get_left("err") == "err"

    left_val = Either.left("error")
    assert left_val.is_left()
    assert not left_val.is_right()
    assert left_val.get_left() == "error"
    assert left_val.get_right(0) == 0

def test_either_map_and_flat_map():
    right_val = Either.right(10)
    mapped = right_val.map(lambda x: x + 5)
    assert mapped.get_right() == 15

    # flat_map возвращает Either
    flat_mapped = right_val.flat_map(lambda x: Either.right(x * 3))
    assert flat_mapped.get_right() == 30

    # map_left для обработки ошибок
    left_val = Either.left("err")
    mapped_left = left_val.map_left(lambda e: f"prefix_{e}")
    assert mapped_left.get_left() == "prefix_err"

def test_either_map_exception_returns_left():
    def bad_func(x):
        return x / 0

    result = Either.right(5).map(bad_func)
    assert result.is_left()
    assert "division by zero" in result.get_left()

# --------------------------
# Тесты для safe_get_document
# --------------------------

def test_safe_get_document():
    docs = (Document(id="doc1", title="Doc 1", text="abc", author="Alice", ts="2025-11-18T12:00:00Z"),
            Document(id="doc2", title="Doc 2", text="def", author="Bob", ts="2025-11-18T12:10:00Z"))


    found = safe_get_document(docs, "doc1")
    assert found.is_just()
    assert found.get().title == "Doc 1"

    not_found = safe_get_document(docs, "doc3")
    assert not_found.is_nothing()

# --------------------------
# Тесты для validate_submission
# --------------------------

def test_validate_submission():
    assert validate_submission("Valid text here", 5).is_right()
    assert validate_submission("", 5).is_left()
    assert validate_submission("short", 10).is_left()
    assert validate_submission("a" * 100001, 1).is_left()

# --------------------------
# Тесты для validate_ngram_size
# --------------------------

def test_validate_ngram_size():
    assert validate_ngram_size(1).is_right()
    assert validate_ngram_size(5).is_right()
    assert validate_ngram_size(0).is_left()
    assert validate_ngram_size(11).is_left()
