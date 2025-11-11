"""
Ленивые вычисления для оптимизации производительности.
Используются генераторы для обработки больших объемов данных.
"""

from typing import Iterator, Callable, Tuple, Dict, Any
from core.domain import Document, Submission, CheckResult
from core.transforms import normalize, tokenize, ngrams, jaccard


def lazy_filter_documents(
    documents: Tuple[Document, ...],
    predicate: Callable[[Document], bool]
) -> Iterator[Document]:
    """
    Ленивая фильтрация документов.
    Возвращает документы по одному, без создания промежуточного списка.
    
    Args:
        documents: Все документы
        predicate: Функция-фильтр
        
    Yields:
        Документы, удовлетворяющие условию
    """
    for doc in documents:
        if predicate(doc):
            yield doc


def lazy_compare_documents(
    submission_text: str,
    documents: Tuple[Document, ...],
    n: int = 3,
    min_similarity: float = 0.0
) -> Iterator[Dict[str, Any]]:
    """
    Ленивое сравнение текста с документами.
    Возвращает результаты по мере проверки каждого документа.
    
    Args:
        submission_text: Проверяемый текст
        documents: База документов
        n: Размер n-грамм
        min_similarity: Минимальная схожесть для включения в результат
        
    Yields:
        Словари с результатами сравнения для каждого документа
    """
    # Подготавливаем n-граммы проверяемого текста один раз
    sub_normalized = normalize(submission_text)
    sub_tokens = tokenize(sub_normalized)
    sub_ngrams = ngrams(sub_tokens, n)
    
    # Сравниваем с каждым документом по очереди
    for idx, doc in enumerate(documents):
        # Обрабатываем документ
        doc_normalized = normalize(doc.text)
        doc_tokens = tokenize(doc_normalized)
        doc_ngrams = ngrams(doc_tokens, n)
        
        # Вычисляем схожесть
        similarity = jaccard(sub_ngrams, doc_ngrams)
        
        # Возвращаем результат, если превышает порог
        if similarity >= min_similarity:
            yield {
                'doc_id': doc.id,
                'doc_title': doc.title,
                'doc_author': doc.author,
                'similarity': similarity,
                'progress': (idx + 1) / len(documents)  # Процент выполнения
            }


def lazy_paginate_documents(
    documents: Tuple[Document, ...],
    page_size: int = 10,
    page: int = 0
) -> Iterator[Document]:
    """
    Ленивая пагинация документов.
    Возвращает только документы для запрошенной страницы.
    
    Args:
        documents: Все документы
        page_size: Количество документов на странице
        page: Номер страницы (начиная с 0)
        
    Yields:
        Документы для запрошенной страницы
    """
    start = page * page_size
    end = start + page_size
    
    for idx, doc in enumerate(documents):
        if start <= idx < end:
            yield doc
        elif idx >= end:
            break


def lazy_search_documents(
    documents: Tuple[Document, ...],
    query: str,
    search_fields: Tuple[str, ...] = ('title', 'author', 'text')
) -> Iterator[Tuple[Document, float]]:
    """
    Ленивый поиск документов с оценкой релевантности.
    Возвращает документы по мере их проверки.
    
    Args:
        documents: Все документы
        query: Поисковый запрос
        search_fields: Поля для поиска
        
    Yields:
        Кортежи (документ, релевантность)
    """
    query_lower = query.lower()
    query_tokens = set(query_lower.split())
    
    for doc in documents:
        relevance = 0.0
        
        # Проверяем каждое поле
        if 'title' in search_fields and query_lower in doc.title.lower():
            relevance += 0.5
        
        if 'author' in search_fields and query_lower in doc.author.lower():
            relevance += 0.3
        
        if 'text' in search_fields:
            doc_tokens = set(doc.text.lower().split())
            matches = len(query_tokens & doc_tokens)
            if matches > 0:
                relevance += 0.2 * (matches / len(query_tokens))
        
        if relevance > 0:
            yield (doc, relevance)


def lazy_batch_process(
    items: Tuple[Any, ...],
    batch_size: int = 5
) -> Iterator[Tuple[Any, ...]]:
    """
    Ленивая обработка элементов батчами.
    Полезно для обработки больших объемов данных частями.
    
    Args:
        items: Все элементы
        batch_size: Размер батча
        
    Yields:
        Батчи элементов
    """
    batch = []
    for item in items:
        batch.append(item)
        if len(batch) >= batch_size:
            yield tuple(batch)
            batch = []
    
    # Возвращаем остаток
    if batch:
        yield tuple(batch)
