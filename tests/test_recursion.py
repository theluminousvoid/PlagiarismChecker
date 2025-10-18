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


def test_flatten_nested_tuples():
    """Тест рекурсивного распрямления вложенных кортежей"""
    nested = (1, (2, (3, 4)), 5)
    flat = flatten_nested_tuples(nested)
    
    assert flat == (1, 2, 3, 4, 5)
    assert all(not isinstance(x, tuple) for x in flat)


def test_flatten_empty_tuple():
    """Тест распрямления пустого кортежа"""
    result = flatten_nested_tuples(tuple())
    assert result == tuple()


def test_flatten_single_element():
    """Тест распрямления кортежа с одним элементом"""
    result = flatten_nested_tuples((5,))
    assert result == (5,)


def test_calculate_similarity_matrix_recursive():
    """Тест рекурсивного построения матрицы схожести"""
    docs = (
        Document("1", "Test1", "hello world", "Author1", "2024-01-01T00:00:00Z"),
        Document("2", "Test2", "hello world", "Author2", "2024-01-02T00:00:00Z"),
        Document("3", "Test3", "goodbye world", "Author3", "2024-01-03T00:00:00Z"),
    )
    
    matrix = calculate_similarity_matrix_recursive(docs, n=2)
    
    assert len(matrix) == 3
    assert len(matrix[0]) == 3
    
    # Диагональ должна быть 1.0 (документ похож на себя на 100%)
    assert matrix[0][0] == 1.0
    assert matrix[1][1] == 1.0
    assert matrix[2][2] == 1.0
    
    # Первый и второй документы очень похожи
    assert matrix[0][1] > 0.8
    assert matrix[1][0] > 0.8


def test_sum_tuple_recursive():
    """Тест рекурсивного суммирования кортежа"""
    data = (1.5, 2.3, 3.7, 4.1)
    result = sum_tuple_recursive(data)
    
    expected = 1.5 + 2.3 + 3.7 + 4.1
    assert abs(result - expected) < 0.0001


def test_sum_empty_tuple():
    """Тест суммирования пустого кортежа"""
    result = sum_tuple_recursive(tuple())
    assert result == 0.0


def test_recursion_with_large_dataset():
    """Тест рекурсии на большом наборе данных"""
    # Создаем большой набор документов
    docs = tuple(
        Document(
            f"doc_{i}",
            f"Title {i}",
            f"text content number {i} with some words",
            f"Author {i %