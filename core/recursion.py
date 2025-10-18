"""
Рекурсивные функции для обхода и сравнения документов.
Лаба №2: Лямбда и замыкания + рекурсия
"""
from typing import Tuple
from core.domain import Document, Submission
from core.transforms import normalize, tokenize, ngrams, jaccard


def compare_submissions_recursive(
    subs: Tuple[Submission, ...],
    docs: Tuple[Document, ...],
    n: int = 3,
    idx: int = 0,
    results: Tuple[float, ...] = None
) -> Tuple[float, ...]:
    """
    Рекурсивное сравнение проверок с документами.
    Возвращает кортеж максимальных схожестей для каждой проверки.
    
    Пример:
        similarities = compare_submissions_recursive(submissions, documents)
        # (0.15, 0.67, 0.23, ...)
    """
    if results is None:
        results = tuple()
    
    # Базовый случай: все проверки обработаны
    if idx >= len(subs):
        return results
    
    # Рекурсивный случай: обработать текущую проверку
    current_sub = subs[idx]
    sub_normalized = normalize(current_sub.text)
    sub_tokens = tokenize(sub_normalized)
    sub_ngrams = ngrams(sub_tokens, n)
    
    # Найти максимальную схожесть с документами
# Найти максимальную схожесть с документами
    max_similarity = _find_max_similarity_recursive(
        sub_ngrams, 
        docs, 
        n, 
        0, 
        0.0,
        current_sub.id  # ДОБАВИЛИ ID
    )
    
    # Добавить результат и продолжить рекурсию
    new_results = results + (max_similarity,)
    return compare_submissions_recursive(subs, docs, n, idx + 1, new_results)


def _find_max_similarity_recursive(
    sub_ngrams: Tuple[str, ...],
    docs: Tuple[Document, ...],
    n: int,
    doc_idx: int,
    current_max: float,
    sub_id: str = None  # ДОБАВИЛИ ПАРАМЕТР
) -> float:
    """
    Рекурсивный поиск максимальной схожести среди документов.
    """
    # Базовый случай: все документы проверены
    if doc_idx >= len(docs):
        return current_max
    
    # Рекурсивный случай: проверить текущий документ
    doc = docs[doc_idx]
    
    # ДОБАВИЛИ: Пропускаем если это тот же документ
    if sub_id and doc.id == sub_id:
        return _find_max_similarity_recursive(
            sub_ngrams,
            docs,
            n,
            doc_idx + 1,
            current_max,
            sub_id
        )
    
    doc_normalized = normalize(doc.text)
    doc_tokens = tokenize(doc_normalized)
    doc_ngrams = ngrams(doc_tokens, n)
    
    similarity = jaccard(sub_ngrams, doc_ngrams)
    new_max = max(current_max, similarity)
    
    # Продолжить рекурсию со следующим документом
    return _find_max_similarity_recursive(
        sub_ngrams,
        docs,
        n,
        doc_idx + 1,
        new_max,
        sub_id  # ДОБАВИЛИ
    )

def tree_walk_documents(
    docs: Tuple[Document, ...],
    root: int = 0,
    visited: Tuple[str, ...] = None,
    depth: int = 0,
    max_depth: int = 5
) -> Tuple[str, ...]:
    """
    Рекурсивный обход "дерева" документов.
    Имитирует обход по связям между документами (по похожим темам).
    
    Пример:
        path = tree_walk_documents(documents, root=0)
        # ('doc_001', 'doc_003', 'doc_007', ...)
    """
    if visited is None:
        visited = tuple()
    
    # Базовые случаи
    if depth >= max_depth or root >= len(docs):
        return visited
    
    current_doc = docs[root]
    
    # Избегаем повторных посещений
    if current_doc.id in visited:
        # Попробовать следующий документ
        if root + 1 < len(docs):
            return tree_walk_documents(docs, root + 1, visited, depth, max_depth)
        return visited
    
    # Добавить текущий документ в путь
    new_visited = visited + (current_doc.id,)
    
    # Найти следующий "связанный" документ (с наибольшей схожестью)
    next_idx = _find_most_similar_doc(current_doc, docs, new_visited)
    
    # Рекурсивный обход
    if next_idx is not None:
        return tree_walk_documents(docs, next_idx, new_visited, depth + 1, max_depth)
    
    return new_visited


def _find_most_similar_doc(
    current: Document,
    docs: Tuple[Document, ...],
    visited: Tuple[str, ...]
) -> int:
    """
    Найти индекс наиболее похожего непосещенного документа.
    """
    current_tokens = tokenize(normalize(current.text))
    current_ngrams = ngrams(current_tokens, 3)
    
    best_idx = None
    best_similarity = 0.0
    
    for idx, doc in enumerate(docs):
        # Пропустить посещенные документы
        if doc.id in visited:
            continue
        
        doc_tokens = tokenize(normalize(doc.text))
        doc_ngrams = ngrams(doc_tokens, 3)
        similarity = jaccard(current_ngrams, doc_ngrams)
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_idx = idx
    
    return best_idx


def count_documents_by_author_recursive(
    docs: Tuple[Document, ...],
    author: str,
    idx: int = 0,
    count: int = 0
) -> int:
    """
    Рекурсивный подсчет документов по автору.
    
    Пример:
        count = count_documents_by_author_recursive(documents, "Кнут")
        # 3
    """
    # Базовый случай
    if idx >= len(docs):
        return count
    
    # Рекурсивный случай
    current_doc = docs[idx]
    new_count = count + (1 if author.lower() in current_doc.author.lower() else 0)
    
    return count_documents_by_author_recursive(docs, author, idx + 1, new_count)


def flatten_nested_tuples(data: Tuple, result: Tuple = None) -> Tuple:
    """
    Рекурсивное "распрямление" вложенных кортежей.
    
    Пример:
        nested = (1, (2, (3, 4)), 5)
        flat = flatten_nested_tuples(nested)
        # (1, 2, 3, 4, 5)
    """
    if result is None:
        result = tuple()
    
    if not data:
        return result
    
    first = data[0]
    rest = data[1:] if len(data) > 1 else tuple()
    
    if isinstance(first, tuple):
        # Рекурсивно обработать вложенный кортеж
        result = flatten_nested_tuples(first, result)
    else:
        # Добавить элемент в результат
        result = result + (first,)
    
    # Рекурсивно обработать остаток
    return flatten_nested_tuples(rest, result)


def calculate_similarity_matrix_recursive(
    docs: Tuple[Document, ...],
    n: int = 3,
    row: int = 0,
    col: int = 0,
    matrix: Tuple[Tuple[float, ...], ...] = None
) -> Tuple[Tuple[float, ...], ...]:
    """
    Рекурсивное построение матрицы схожести между документами.
    Возвращает кортеж кортежей (матрицу).
    
    Пример:
        matrix = calculate_similarity_matrix_recursive(documents[:5])
        # ((1.0, 0.2, 0.1, ...), (0.2, 1.0, 0.3, ...), ...)
    """
    if matrix is None:
        # Инициализировать пустую матрицу
        matrix = tuple(tuple() for _ in range(len(docs)))
    
    # Базовый случай: все строки обработаны
    if row >= len(docs):
        return matrix
    
    # Базовый случай для текущей строки: все столбцы обработаны
    if col >= len(docs):
        return calculate_similarity_matrix_recursive(docs, n, row + 1, 0, matrix)
    
    # Вычислить схожесть
    if row == col:
        similarity = 1.0  # Документ полностью похож на себя
    else:
        doc1_tokens = tokenize(normalize(docs[row].text))
        doc2_tokens = tokenize(normalize(docs[col].text))
        doc1_ngrams = ngrams(doc1_tokens, n)
        doc2_ngrams = ngrams(doc2_tokens, n)
        similarity = jaccard(doc1_ngrams, doc2_ngrams)
    
    # Добавить значение в матрицу (создать новый кортеж для неизменяемости)
    current_row = matrix[row]
    new_row = current_row + (similarity,)
    new_matrix = matrix[:row] + (new_row,) + matrix[row + 1:]
    
    # Рекурсивно обработать следующий столбец
    return calculate_similarity_matrix_recursive(docs, n, row, col + 1, new_matrix)


def sum_tuple_recursive(data: Tuple[float, ...], idx: int = 0, total: float = 0.0) -> float:
    """
    Рекурсивное суммирование элементов кортежа.
    
    Пример:
        result = sum_tuple_recursive((1.5, 2.3, 3.7))
        # 7.5
    """
    # Базовый случай
    if idx >= len(data):
        return total
    
    # Рекурсивный случай
    return sum_tuple_recursive(data, idx + 1, total + data[idx])