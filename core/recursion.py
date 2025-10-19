"""
Рекурсивные функции для обхода и сравнения документов.
Лямбда и замыкания + рекурсия
Использование композиции функций
"""
from typing import Tuple
from core.domain import Document, Submission
from core.transforms import normalize, tokenize, ngrams, jaccard
from core.compose import text_processing_pipeline


def _text_to_ngrams(text: str, n: int = 3) -> Tuple[Tuple[str, ...], ...]:
    """
    Вспомогательная функция: преобразует текст в n-граммы через пайплайн.
    Использует композицию
    """
    _, _, grams = text_processing_pipeline(text, n)
    return grams


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
    
    Использует: рекурсия, композиция
    
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
    
    # Используем композицию вместо трех отдельных вызовов
    sub_ngrams = _text_to_ngrams(current_sub.text, n)
    
    # Найти максимальную схожесть с документами
    max_similarity = _find_max_similarity_recursive(
        sub_ngrams, 
        docs, 
        n, 
        0, 
        0.0,
        current_sub.id
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
    sub_id: str = None
) -> float:
    """
    Рекурсивный поиск максимальной схожести среди документов.
    Использует композицию для обработки текста.
    """
    # Базовый случай: все документы проверены
    if doc_idx >= len(docs):
        return current_max
    
    # Рекурсивный случай: проверить текущий документ
    doc = docs[doc_idx]
    
    # Пропускаем если это тот же документ
    if sub_id and doc.id == sub_id:
        return _find_max_similarity_recursive(
            sub_ngrams,
            docs,
            n,
            doc_idx + 1,
            current_max,
            sub_id
        )
    
    # Используем композицию
    doc_ngrams = _text_to_ngrams(doc.text, n)
    
    similarity = jaccard(sub_ngrams, doc_ngrams)
    new_max = max(current_max, similarity)
    
    # Продолжить рекурсию со следующим документом
    return _find_max_similarity_recursive(
        sub_ngrams,
        docs,
        n,
        doc_idx + 1,
        new_max,
        sub_id
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
    
    Использует: рекурсия, композиция
    
    Пример:
        path = tree_walk_documents(documents, root=0)
        # ('doc_001', 'doc_003', 'doc_007', ...)
    """
    if visited is None:
        visited = tuple()
    
    # Базовые случаи
    if depth >= max_depth:
        return visited
    
    if root >= len(docs):
        return visited
    
    current_doc = docs[root]
    
    # Избегаем повторных посещений
    if current_doc.id in visited:
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
    Использует композицию для обработки текста.
    """
    current_ngrams = _text_to_ngrams(current.text, 3)
    
    best_idx = None
    best_similarity = 0.0
    
    for idx, doc in enumerate(docs):
        # Пропустить посещенные документы
        if doc.id in visited:
            continue
        
        doc_ngrams = _text_to_ngrams(doc.text, 3)
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
