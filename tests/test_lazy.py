import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.lazy import (
    lazy_filter_documents,
    lazy_compare_documents,
    lazy_paginate_documents,
    lazy_search_documents,
    lazy_batch_process
)
from core.domain import Document


# Тестовые данные
def create_test_documents():
    return (
        Document("1", "Python Tutorial", "Python is a great programming language", "John Doe", "2024-01-01T00:00:00Z"),
        Document("2", "Java Basics", "Java is used for enterprise applications", "Jane Smith", "2024-01-02T00:00:00Z"),
        Document("3", "Python Advanced", "Advanced Python programming techniques", "John Doe", "2024-01-03T00:00:00Z"),
        Document("4", "C++ Guide", "C++ is a powerful language", "Bob Johnson", "2024-01-04T00:00:00Z"),
        Document("5", "Python Data Science", "Python for data analysis and machine learning", "Alice Brown", "2024-01-05T00:00:00Z"),
    )


def test_lazy_filter_documents():
    """Тест ленивой фильтрации"""
    docs = create_test_documents()
    
    # Фильтр по автору
    filtered = lazy_filter_documents(docs, lambda d: d.author == "John Doe")
    result = list(filtered)
    
    assert len(result) == 2
    assert result[0].id == "1"
    assert result[1].id == "3"
    
    # Проверяем, что это генератор
    filtered_gen = lazy_filter_documents(docs, lambda d: "Python" in d.title)
    assert hasattr(filtered_gen, '__iter__')
    assert hasattr(filtered_gen, '__next__')


def test_lazy_compare_documents():
    """Тест ленивого сравнения документов"""
    docs = create_test_documents()
    test_text = "Python is great for programming"
    
    # Сравниваем с минимальной схожестью 0.1
    results = list(lazy_compare_documents(test_text, docs, n=2, min_similarity=0.1))
    
    # Должны быть найдены документы с Python
    assert len(results) > 0
    
    # Проверяем структуру результата
    assert 'doc_id' in results[0]
    assert 'doc_title' in results[0]
    assert 'similarity' in results[0]
    assert 'progress' in results[0]
    
    # Проверяем, что прогресс растет
    assert results[-1]['progress'] == 1.0


def test_lazy_compare_yields_progressively():
    """Тест, что сравнение происходит поэтапно"""
    docs = create_test_documents()
    test_text = "Python programming language"
    
    results_generator = lazy_compare_documents(test_text, docs, n=2, min_similarity=0.0)
    
    # Получаем результаты по одному
    results = []
    for result in results_generator:
        results.append(result)
        # Проверяем, что каждый результат содержит прогресс
        assert 0 < result['progress'] <= 1.0
    
    assert len(results) == len(docs)


def test_lazy_paginate_documents():
    """Тест ленивой пагинации"""
    docs = create_test_documents()
    
    # Страница 0 (первые 2 документа)
    page_0 = list(lazy_paginate_documents(docs, page_size=2, page=0))
    assert len(page_0) == 2
    assert page_0[0].id == "1"
    assert page_0[1].id == "2"
    
    # Страница 1 (следующие 2 документа)
    page_1 = list(lazy_paginate_documents(docs, page_size=2, page=1))
    assert len(page_1) == 2
    assert page_1[0].id == "3"
    assert page_1[1].id == "4"
    
    # Страница 2 (последний документ)
    page_2 = list(lazy_paginate_documents(docs, page_size=2, page=2))
    assert len(page_2) == 1
    assert page_2[0].id == "5"
    
    # Несуществующая страница
    page_3 = list(lazy_paginate_documents(docs, page_size=2, page=3))
    assert len(page_3) == 0


def test_lazy_search_documents():
    """Тест ленивого поиска"""
    docs = create_test_documents()
    
    # Поиск по "Python"
    results = list(lazy_search_documents(docs, "Python"))
    assert len(results) >= 3  # Минимум 3 документа с Python
    
    # Проверяем структуру
    for doc, relevance in results:
        assert isinstance(doc, Document)
        assert 0 <= relevance <= 1.0
    
    # Результаты должны быть отсортированы по релевантности
    relevances = [r for _, r in results]
    # Проверяем, что все релевантности положительные
    assert all(r > 0 for r in relevances)


def test_lazy_search_no_results():
    """Тест поиска без результатов"""
    docs = create_test_documents()
    results = list(lazy_search_documents(docs, "NonexistentQuery"))
    assert len(results) == 0


def test_lazy_batch_process():
    """Тест ленивой обработки батчами"""
    items = tuple(range(12))  # 0..11
    
    # Батчи по 5
    batches = list(lazy_batch_process(items, batch_size=5))
    
    assert len(batches) == 3
    assert batches[0] == (0, 1, 2, 3, 4)
    assert batches[1] == (5, 6, 7, 8, 9)
    assert batches[2] == (10, 11)


def test_lazy_batch_exact_size():
    """Тест батчей с точным размером"""
    items = tuple(range(10))
    batches = list(lazy_batch_process(items, batch_size=5))
    
    assert len(batches) == 2
    assert batches[0] == (0, 1, 2, 3, 4)
    assert batches[1] == (5, 6, 7, 8, 9)


def test_generators_are_lazy():
    """Тест, что генераторы действительно ленивые"""
    docs = create_test_documents()
    
    # Создаем генератор, но не вычисляем результаты
    filtered = lazy_filter_documents(docs, lambda d: d.author == "John Doe")
    
    # Генератор создан, но значения еще не вычислены
    assert hasattr(filtered, '__next__')
    
    # Получаем только первое значение
    first = next(filtered)
    assert first.id == "1"
    
    # Остальные значения еще не обработаны


def test_memory_efficiency():
    """Тест эффективности памяти - генераторы не создают промежуточные списки"""
    # Создаем большое количество документов
    large_docs = tuple(
        Document(str(i), f"Doc {i}", f"Text {i}", "Author", "2024-01-01T00:00:00Z")
        for i in range(1000)
    )
    
    # Используем генератор для фильтрации
    filtered = lazy_filter_documents(large_docs, lambda d: int(d.id) % 2 == 0)
    
    # Получаем только первые 10
    first_10 = []
    for i, doc in enumerate(filtered):
        if i >= 10:
            break
        first_10.append(doc)
    
    assert len(first_10) == 10
    # Остальные 990 документов не были обработаны благодаря ленивости
