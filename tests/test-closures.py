import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.closures import (
    by_author, by_date_range, by_min_length, 
    by_title_contains, compose_filters, any_filter,
    make_submission_filter
)
from core.domain import Document, Submission


def test_by_author_filter():
    docs = (
        Document("1", "Test1", "text", "Кнут", "2024-01-01T00:00:00Z"),
        Document("2", "Test2", "text", "Мартин", "2024-01-02T00:00:00Z"),
        Document("3", "Test3", "text", "Дональд Кнут", "2024-01-03T00:00:00Z"),
    )
    
    filter_knut = by_author("Кнут")
    filtered = tuple(filter(filter_knut, docs))
    
    assert len(filtered) == 2
    assert filtered[0].id == "1"
    assert filtered[1].id == "3"


def test_by_date_range_filter():
    docs = (
        Document("1", "Test1", "text", "Author", "2024-01-01T00:00:00Z"),
        Document("2", "Test2", "text", "Author", "2024-06-15T00:00:00Z"),
        Document("3", "Test3", "text", "Author", "2024-12-31T00:00:00Z"),
    )
    
    filter_mid = by_date_range("2024-06-01", "2024-07-01")
    filtered = tuple(filter(filter_mid, docs))
    
    assert len(filtered) == 1
    assert filtered[0].id == "2"


def test_by_min_length_filter():
    docs = (
        Document("1", "Test1", "short", "Author", "2024-01-01T00:00:00Z"),
        Document("2", "Test2", "this is a longer text with many words", "Author", "2024-01-02T00:00:00Z"),
    )
    
    filter_long = by_min_length(20)
    filtered = tuple(filter(filter_long, docs))
    
    assert len(filtered) == 1
    assert filtered[0].id == "2"


def test_by_title_contains():
    docs = (
        Document("1", "Python Programming", "text", "Author", "2024-01-01T00:00:00Z"),
        Document("2", "Java Basics", "text", "Author", "2024-01-02T00:00:00Z"),
        Document("3", "Advanced Python", "text", "Author", "2024-01-03T00:00:00Z"),
    )
    
    filter_python = by_title_contains("Python")
    filtered = tuple(filter(filter_python, docs))
    
    assert len(filtered) == 2
    assert filtered[0].id == "1"
    assert filtered[1].id == "3"


def test_compose_filters():
    docs = (
        Document("1", "Short", "abc", "Кнут", "2024-01-01T00:00:00Z"),
        Document("2", "Long Python", "this is a long text about programming", "Кнут", "2024-01-02T00:00:00Z"),
        Document("3", "Long Java", "this is also a long text but different", "Мартин", "2024-01-03T00:00:00Z"),
    )
    
    combined = compose_filters(
        by_author("Кнут"),
        by_min_length(20)
    )
    filtered = tuple(filter(combined, docs))
    
    assert len(filtered) == 1
    assert filtered[0].id == "2"


def test_any_filter():
    docs = (
        Document("1", "Test", "text", "Кнут", "2024-01-01T00:00:00Z"),
        Document("2", "Test", "text", "Мартин", "2024-01-02T00:00:00Z"),
        Document("3", "Test", "text", "Эйнштейн", "2024-01-03T00:00:00Z"),
    )
    
    combined = any_filter(
        by_author("Кнут"),
        by_author("Мартин")
    )
    filtered = tuple(filter(combined, docs))
    
    assert len(filtered) == 2


def test_make_submission_filter():
    subs = (
        Submission("1", "user_001", "short", "2024-01-01T00:00:00Z"),
        Submission("2", "user_001", "this is a longer submission text", "2024-01-02T00:00:00Z"),
        Submission("3", "user_002", "another long submission text here", "2024-01-03T00:00:00Z"),
    )
    
    filter_user = make_submission_filter(user_id="user_001", min_length=20)
    filtered = tuple(filter(filter_user, subs))
    
    assert len(filtered) == 1
    assert filtered[0].id == "2"
