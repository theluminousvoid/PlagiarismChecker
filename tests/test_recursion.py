import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.recursion import (
    compare_submissions_recursive,
    tree_walk_documents,
    count_documents_by_author_recursive,
    flatten_nested_tuples,
    calculate_similarity_matrix_recursive,
    sum_tuple_recursive
)
from core.domain import Document, Submission


def test_compare_submissions_recursive():
    """Тест рекурсивного сравнения проверок с документами"""
    docs = (
        Document("1", "Test1", "hello world", "Author1", "2024-01-01T00:00:00Z"),
        Document("2", "Test2", "goodbye world", "Author2", "2024-01-02T00:00:00Z"),
    )
    
    subs = (
        Submission("s1", "u1", "hello world", "2024-01-01T00:00:00Z"),
        Submission("s2", "u2", "something different", "2024-01-02T00:00:00Z"),
    )
    
    results = compare_submissions_recursive(subs, docs, n=2)
    
    assert len(results) == 2
    assert results[0] > 0.5  # Первая проверка очень похожа на первый документ
    assert 0 <= results[1] <= 1  # Вторая проверка имеет меньшую схожесть


def test_tree_walk_documents():
    """Тест рекурсивного обхода дерева документов"""
    docs = (
        Document("1", "Python", "python programming language", "Author1", "2024-01-01T00:00:00Z"),
        Document("2", "Java", "java programming language", "Author2", "2024-01-02T00:00:00Z"),
        Document("3", "C++", "cpp programming language", "Author3", "2024-01-03T00:00:00Z"),
    )
    
    path = tree_walk_documents(docs, root=0, max_depth=3)
    
    assert len(path) > 0
    assert path[0] == "1"  # Начинаем с первого документа
    assert len(path) <= 3  # Не больше max_depth


def test_count_documents_by_author_recursive():
    """Тест рекурсивного подсчета документов по автору"""
    docs = (
        Document("1", "Test1", "text", "Donald Knuth", "2024-01-01T00:00:00Z"),
        Document("2", "Test2", "text", "Robert Martin", "2024-01-02T00:00:00Z"),
        Document("3", "Test3", "text", "Donald Knuth", "2024-01-03T00:00:00Z"),
    )
    
    count = count_documents_by_author_recursive(docs, "Knuth")
    
    assert count == 2

