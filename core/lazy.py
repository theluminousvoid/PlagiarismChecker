"""
Оптимизация производительности через генераторы.
Внутренний модуль - пользователь не видит технических деталей.
"""

from typing import Iterator, Callable, Tuple, Dict, Any
from core.domain import Document
from core.transforms import normalize, tokenize, ngrams, jaccard


def paginate_documents(
    documents: Tuple[Document, ...],
    page_size: int = 10,
    page: int = 0
) -> Iterator[Document]:
    """
    Пагинация документов с ленивой загрузкой.
    Возвращает только нужную страницу вместо всех документов.
    """
    start = page * page_size
    end = start + page_size
    
    for idx, doc in enumerate(documents):
        if start <= idx < end:
            yield doc
        elif idx >= end:
            break


def search_documents(
    documents: Tuple[Document, ...],
    query: str,
    search_fields: Tuple[str, ...] = ('title', 'author', 'text')
) -> Iterator[Tuple[Document, float]]:
    """
    Поиск документов с оценкой релевантности.
    Возвращает результаты по мере нахождения совпадений.
    """
    if not query or not query.strip():
        return
    
    query_lower = query.lower().strip()
    query_tokens = set(query_lower.split())
    
    for doc in documents:
        relevance = 0.0
        
        # Проверяем название (наивысший приоритет)
        if 'title' in search_fields and query_lower in doc.title.lower():
            relevance += 0.5
        
        # Проверяем автора
        if 'author' in search_fields and query_lower in doc.author.lower():
            relevance += 0.3
        
        # Проверяем текст
        if 'text' in search_fields:
            doc_tokens = set(doc.text.lower().split())
            matches = len(query_tokens & doc_tokens)
            if matches > 0:
                relevance += 0.2 * (matches / len(query_tokens))
        
        if relevance > 0:
            yield (doc, relevance)


def progressive_check(
    submission_text: str,
    documents: Tuple[Document, ...],
    n: int = 3,
    min_similarity: float = 0.0
) -> Iterator[Dict[str, Any]]:
    """
    Проверка на плагиат с прогрессом в реальном времени.
    Возвращает результаты по мере проверки каждого документа.
    """
    # Подготавливаем n-граммы один раз
    sub_normalized = normalize(submission_text)
    sub_tokens = tokenize(sub_normalized)
    sub_ngrams = ngrams(sub_tokens, n)
    
    total = len(documents)
    
    # Проверяем каждый документ
    for idx, doc in enumerate(documents):
        doc_normalized = normalize(doc.text)
        doc_tokens = tokenize(doc_normalized)
        doc_ngrams = ngrams(doc_tokens, n)
        
        similarity = jaccard(sub_ngrams, doc_ngrams)
        
        # Возвращаем только значимые результаты
        if similarity >= min_similarity:
            yield {
                'doc_id': doc.id,
                'doc_title': doc.title,
                'doc_author': doc.author,
                'similarity': similarity,
                'progress': round((idx + 1) / total * 100, 1)
            }


def filter_documents(
    documents: Tuple[Document, ...],
    predicate: Callable[[Document], bool]
) -> Iterator[Document]:
    """
    Фильтрация документов без создания промежуточного списка.
    Обрабатывает документы по одному.
    """
    for doc in documents:
        if predicate(doc):
            yield doc


def batch_process(
    items: Tuple[Any, ...],
    batch_size: int = 5
) -> Iterator[Tuple[Any, ...]]:
    """
    Обработка элементов батчами для экономии памяти.
    """
    batch = []
    for item in items:
        batch.append(item)
        if len(batch) >= batch_size:
            yield tuple(batch)
            batch = []
    
    if batch:
        yield tuple(batch)