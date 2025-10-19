"""
Замыкания и фильтры для работы с документами
Лаба №2: Лямбда и замыкания + рекурсия
"""

from typing import Callable
from core.domain import Document


def by_author(author: str) -> Callable[[Document], bool]:
    """
    Замыкание для фильтрации документов по автору.
    
    Args:
        author: Имя автора для поиска
        
    Returns:
        Функция-фильтр
        
    Example:
        filter_knuth = by_author("Knuth")
        knuth_docs = list(filter(filter_knuth, documents))
    """
    def filter_func(doc: Document) -> bool:
        return author.lower() in doc.author.lower()
    return filter_func


def by_title(keyword: str) -> Callable[[Document], bool]:
    """
    Замыкание для фильтрации документов по названию.
    
    Args:
        keyword: Ключевое слово в названии
        
    Returns:
        Функция-фильтр
    """
    def filter_func(doc: Document) -> bool:
        return keyword.lower() in doc.title.lower()
    return filter_func


def by_min_length(min_len: int) -> Callable[[Document], bool]:
    """
    Замыкание для фильтрации документов по минимальной длине.
    
    Args:
        min_len: Минимальная длина текста
        
    Returns:
        Функция-фильтр
    """
    def filter_func(doc: Document) -> bool:
        return len(doc.text) >= min_len
    return filter_func


def by_date_range(start: str, end: str) -> Callable[[Document], bool]:
    """
    Замыкание для фильтрации документов по диапазону дат.
    
    Args:
        start: Начальная дата (ISO format)
        end: Конечная дата (ISO format)
        
    Returns:
        Функция-фильтр
    """
    def filter_func(doc: Document) -> bool:
        return start <= doc.ts <= end
    return filter_func


def compose_filters(*filters: Callable[[Document], bool]) -> Callable[[Document], bool]:
    """
    Композиция нескольких фильтров в один.
    Документ должен пройти ВСЕ фильтры.
    
    Args:
        *filters: Произвольное количество функций-фильтров
        
    Returns:
        Композитная функция-фильтр
        
    Example:
        combined = compose_filters(
            by_author("Knuth"),
            by_min_length(1000),
            by_title("Algorithm")
        )
        filtered_docs = list(filter(combined, documents))
    """
    def combined_filter(doc: Document) -> bool:
        return all(f(doc) for f in filters)
    return combined_filter


def create_similarity_threshold(threshold: float) -> Callable[[float], bool]:
    """
    Замыкание для фильтрации по порогу схожести.
    
    Args:
        threshold: Порог схожести (0-1)
        
    Returns:
        Функция для проверки схожести
    """
    def check_threshold(similarity: float) -> bool:
        return similarity >= threshold
    return check_threshold
