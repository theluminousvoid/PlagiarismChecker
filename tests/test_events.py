import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.events import (
    Event, EventBus,
    handle_text_submitted, handle_check_done, handle_alert,
    get_recent_submissions, get_check_results, get_suspicious_matches,
    get_activity_stats
)


def test_event_creation():
    """Тест создания события"""
    event = Event(
        name='TEST_EVENT',
        ts='2024-01-01T00:00:00Z',
        payload={'key': 'value'}
    )
    
    assert event.name == 'TEST_EVENT'
    assert event.payload['key'] == 'value'


def test_event_bus_subscribe():
    """Тест подписки на события"""
    bus = EventBus()
    
    received = []
    
    def handler(event, payload):
        received.append(payload)
        return {'handled': True}
    
    bus.subscribe('TEST', handler)
    bus.publish('TEST', {'data': 'test'})
    
    assert len(received) == 1
    assert received[0]['data'] == 'test'


def test_event_bus_multiple_handlers():
    """Тест множественных обработчиков"""
    bus = EventBus()
    
    results = []
    
    def handler1(event, payload):
        results.append('handler1')
        return {'id': 1}
    
    def handler2(event, payload):
        results.append('handler2')
        return {'id': 2}
    
    bus.subscribe('TEST', handler1)
    bus.subscribe('TEST', handler2)
    
    outputs = bus.publish('TEST', {})
    
    assert len(results) == 2
    assert len(outputs) == 2
    assert outputs[0]['id'] == 1
    assert outputs[1]['id'] == 2


def test_event_history():
    """Тест истории событий"""
    bus = EventBus()
    
    bus.publish('EVENT1', {'data': 'first'})
    bus.publish('EVENT2', {'data': 'second'})
    bus.publish('EVENT1', {'data': 'third'})
    
    # Вся история
    all_history = bus.get_history()
    assert len(all_history) == 3
    
    # Фильтр по имени
    event1_history = bus.get_history('EVENT1')
    assert len(event1_history) == 2
    
    # С лимитом
    limited = bus.get_history(limit=2)
    assert len(limited) == 2


def test_handle_text_submitted():
    """Тест обработчика загрузки текста"""
    event = Event(
        name='TEXT_SUBMITTED',
        ts='2024-01-01T00:00:00Z',
        payload={
            'user_id': 'user_001',
            'doc_id': 'doc_001',
            'title': 'Test Document',
            'text': 'This is a test document with some text.'
        }
    )
    
    result = handle_text_submitted(event, event.payload)
    
    assert result['type'] == 'new_submission'
    assert result['user_id'] == 'user_001'
    assert result['doc_id'] == 'doc_001'
    assert result['title'] == 'Test Document'
    assert result['text_length'] > 0


def test_handle_check_done():
    """Тест обработчика завершения проверки"""
    event = Event(
        name='CHECK_DONE',
        ts='2024-01-01T00:00:00Z',
        payload={
            'doc_id': 'doc_001',
            'similarity': 0.85,
            'admin_id': 'admin_001'
        }
    )
    
    result = handle_check_done(event, event.payload)
    
    assert result['type'] == 'check_result'
    assert result['similarity'] == 0.85
    assert result['status'] == 'suspicious'  # > 0.7


def test_handle_alert():
    """Тест обработчика алертов"""
    event = Event(
        name='ALERT',
        ts='2024-01-01T00:00:00Z',
        payload={
            'severity': 'high',
            'message': 'Высокая схожесть обнаружена',
            'doc_id': 'doc_001',
            'similarity': 0.95
        }
    )
    
    result = handle_alert(event, event.payload)
    
    assert result['type'] == 'alert'
    assert result['severity'] == 'high'
    assert result['requires_attention'] is True  # > 0.8


def test_get_suspicious_matches():
    """Тест витрины подозрительных совпадений"""
    from core.events import event_bus
    
    # Очищаем историю перед тестом
    event_bus.clear_history()
    
    # Добавляем обработчики
    event_bus.subscribe('CHECK_DONE', handle_check_done)
    event_bus.subscribe('ALERT', handle_alert)
    
    # Публикуем события
    event_bus.publish('CHECK_DONE', {
        'doc_id': 'doc_001',
        'similarity': 0.75,
        'admin_id': 'admin_001'
    })
    
    event_bus.publish('ALERT', {
        'doc_id': 'doc_002',
        'similarity': 0.90,
        'message': 'Критическое совпадение',
        'requires_attention': True
    })
    
    # Проверяем витрину
    suspicious = get_suspicious_matches(threshold=0.7)
    
    assert len(suspicious) > 0
    assert all(s['similarity'] >= 0.7 for s in suspicious)


def test_event_bus_error_handling():
    """Тест обработки ошибок в handlers"""
    bus = EventBus()
    
    def failing_handler(event, payload):
        raise ValueError("Handler error")
    
    def working_handler(event, payload):
        return {'status': 'ok'}
    
    bus.subscribe('TEST', failing_handler)
    bus.subscribe('TEST', working_handler)
    
    results = bus.publish('TEST', {})
    
    # Оба обработчика должны быть вызваны
    assert len(results) == 2
    # Первый вернул ошибку
    assert 'error' in results[0]
    # Второй отработал нормально
    assert results[1]['status'] == 'ok'


def test_activity_stats():
    """Тест статистики активности"""
    from core.events import event_bus
    
    # Очищаем историю перед тестом
    event_bus.clear_history()
    
    event_bus.subscribe('TEXT_SUBMITTED', handle_text_submitted)
    event_bus.subscribe('CHECK_DONE', handle_check_done)
    event_bus.subscribe('ALERT', handle_alert)
    
    # Генерируем события
    event_bus.publish('TEXT_SUBMITTED', {'user_id': 'u1', 'doc_id': 'd1', 'title': 'T1', 'text': 'text'})
    event_bus.publish('TEXT_SUBMITTED', {'user_id': 'u2', 'doc_id': 'd2', 'title': 'T2', 'text': 'text'})
    event_bus.publish('CHECK_DONE', {'doc_id': 'd1', 'similarity': 0.5, 'admin_id': 'a1'})
    event_bus.publish('ALERT', {'doc_id': 'd1', 'similarity': 0.8, 'message': 'Alert'})
    
    stats = get_activity_stats()
    
    assert stats['total_events'] == 4
    assert stats['submissions'] == 2
    assert stats['checks'] == 1
    assert stats['alerts'] == 1
    assert stats['last_activity'] is not None


def test_clear_history():
    """Тест очистки истории"""
    bus = EventBus()
    
    bus.publish('TEST', {'data': '1'})
    bus.publish('TEST', {'data': '2'})
    
    assert len(bus.get_history()) == 2
    
    bus.clear_history()
    
    assert len(bus.get_history()) == 0
