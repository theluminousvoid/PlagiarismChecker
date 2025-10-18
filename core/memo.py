"""
Мемоизация для оптимизации повторных проверок
Лаба №3: Продвинутая рекурсия + мемоизация
"""

from functools import lru_cache
from typing import Tuple, Dict
from core.domain import Document, Submission
from core.transforms import normalize, tokenize, ngrams, jaccard

# Глобальный кэш для статистики
_cache_stats = {"hits": 0, "misses": 0, "size": 0}


@lru_cache(maxsize=1000)
def _compare_texts_cached(text1: str, text2: str, n: int) -> float:
    """
    Кэшированное сравнение двух текстов.
    Использует @lru_cache для автоматической мемоизации.
    
    Args:
        text1: Первый текст
        text2: Второй текст
        n: Размер n-грамм
        
    Returns:
        Коэффициент схожести (0-1)
    """
    # Обновляем статистику
    cache_info = _compare_texts_cached.cache_info()
    _cache_stats["hits"] = cache_info.hits
    _cache_stats["misses"] = cache_info.misses
    _cache_stats["size"] = cache_info.currsize
    
    # Выполняем сравнение
    normalized1 = normalize(text1)
    normalized2 = normalize(text2)
    tokens1 = tokenize(normalized1)
    tokens2 = tokenize(normalized2)
    ngrams1 = ngrams(tokens1, n)
    ngrams2 = ngrams(tokens2, n)
    
    return jaccard(ngrams1, ngrams2)


def check_submission_cached(
    submission: Submission,
    documents: Tuple[Document, ...],
    n: int = 3
) -> Dict:
    """
    Проверка submission с использованием кэша.
    
    Args:
        submission: Проверяемый текст
        documents: База документов для сравнения
        n: Размер n-грамм
        
    Returns:
        Словарь с результатами проверки
    """
    results = []
    
    # Сравниваем с каждым документом
    for doc in documents:
        similarity = _compare_texts_cached(submission.text, doc.text, n)
        results.append({
            'doc_id': doc.id,
            'doc_title': doc.title,
            'doc_author': doc.author,
            'similarity': similarity
        })
    
    # Сортируем по убыванию схожести
    results.sort(key=lambda x: x['similarity'], reverse=True)
    
    # Находим максимальную схожесть
    max_similarity = results[0]['similarity'] if results else 0.0
    
    # Статистика
    tokens = tokenize(normalize(submission.text))
    text_ngrams = ngrams(tokens, n)
    
    return {
        'score': max_similarity,
        'matches': results[:5],  # Топ-5 похожих
        'stats': {
            'tokens': len(tokens),
            'ngrams': len(text_ngrams),
            'documents_checked': len(documents),
            'cache_used': True,
            **_cache_stats
        }
    }


def get_cache_stats() -> Dict:
    """Получить статистику кэша"""
    cache_info = _compare_texts_cached.cache_info()
    return {
        "hits": cache_info.hits,
        "misses": cache_info.misses,
        "size": cache_info.currsize,
        "maxsize": cache_info.maxsize,
        "hit_rate": cache_info.hits / (cache_info.hits + cache_info.misses) 
                    if (cache_info.hits + cache_info.misses) > 0 else 0
    }
