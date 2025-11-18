import pytest
from datetime import datetime, timedelta
import core.events

def reset_bus():
    # Подменяем глобальную шину чистой инстанцией и регистрируем хэндлеры
    core.events.event_bus = core.events.EventBus()
    core.events.setup_event_handlers()

def test_publish_text_submitted_adds_submission_and_history():
    reset_bus()
    payload = {
        'doc_id': 'd1',
        'title': 'Тест',
        'user_id': 'u1',
        'username': 'ivan',
        'full_name': 'Иван Иванов',
        'text': 'hello'
    }

    core.events.event_bus.publish('TEXT_SUBMITTED', payload)

    # История содержит событие
    assert len(core.events.event_bus._event_history) == 1
    ev = core.events.event_bus._event_history[0]
    assert ev.name == 'TEXT_SUBMITTED'
    assert ev.payload['doc_id'] == 'd1'

    # Мониторинг заполнился
    subs = core.events.event_bus.monitoring_data.submissions
    assert len(subs) == 1
    sub = subs[0]
    assert sub['doc_id'] == 'd1'
    assert sub['username'] == 'ivan'
    assert sub['text_length'] == len('hello')

def test_check_done_creates_check_and_alert_when_similarity_high():
    reset_bus()
    payload = {
        'doc_id': 'doc-42',
        'doc_title': 'Пример',
        'author_username': 'alice',
        'author_full_name': 'Alice',
        'similarity': 0.82,
        'admin_id': 'adm1',
        'admin_name': 'Admin'
    }

    core.events.event_bus.publish('CHECK_DONE', payload)

    # Проверки и алерты должны добавиться
    checks = core.events.event_bus.monitoring_data.check_results
    alerts = core.events.event_bus.monitoring_data.alerts

    assert len(checks) == 1
    assert checks[0]['doc_id'] == 'doc-42'
    assert checks[0]['status'] in ('high', 'medium', 'low')

    # similarity 0.82 > 0.7 -> alert должен появиться
    assert len(alerts) == 1
    a = alerts[0]
    assert a['doc_id'] == 'doc-42'
    assert a['severity'] in ('high', 'medium')
    assert a['requires_attention'] is True

def test_alert_handler_adds_alert_with_requires_attention_logic():
    reset_bus()
    payload = {
        'doc_id': 'doc-X',
        'doc_title': 'X',
        'author_username': 'bob',
        'author_full_name': 'Bob',
        'similarity': 0.86,
        'severity': 'high',
        'message': 'Нужна проверка'
    }

    core.events.event_bus.publish('ALERT', payload)

    alerts = core.events.event_bus.monitoring_data.alerts
    assert len(alerts) == 1
    assert alerts[0]['doc_id'] == 'doc-X'
    # В обработчике requires_attention = similarity > 0.8
    assert alerts[0]['requires_attention'] is True
    assert alerts[0]['message'] == 'Нужна проверка'

def test_get_suspicious_matches_dedup_and_sorting():
    reset_bus()
    md = core.events.event_bus.monitoring_data

    # Добавляем два результата проверки для одного doc и второй для другого doc
    ts1 = (datetime.utcnow() - timedelta(minutes=10)).isoformat() + 'Z'
    ts2 = (datetime.utcnow() - timedelta(minutes=5)).isoformat() + 'Z'
    ts3 = datetime.utcnow().isoformat() + 'Z'

    md.add_check_result({
        'type': 'check_result', 'doc_id': 'A', 'similarity': 0.75, 'timestamp': ts1
    })
    md.add_check_result({
        'type': 'check_result', 'doc_id': 'A', 'similarity': 0.8, 'timestamp': ts2
    })
    md.add_check_result({
        'type': 'check_result', 'doc_id': 'B', 'similarity': 0.7, 'timestamp': ts3
    })

    # Также добавим альерт для doc A (дубликат по doc_id)
    md.add_alert({
        'type': 'alert', 'doc_id': 'A', 'similarity': 0.85, 'timestamp': ts3
    })

    # threshold 0.7 -> должны попасть B (0.7) и A (0.75/0.8/0.85) но без дублей, сортированные по timestamp desc
    suspicious = core.events.get_suspicious_matches(threshold=0.7)
    assert isinstance(suspicious, list)
    # doc A и B — только уникальные doc_id
    doc_ids = [x['doc_id'] for x in suspicious]
    assert 'A' in doc_ids and 'B' in doc_ids
    assert len(set(doc_ids)) == len(doc_ids)
    # Поскольку ts3 новее — на первом месте должен быть элемент с timestamp == ts3
    assert suspicious[0]['timestamp'] == ts3

def test_event_history_limit_and_get_activity_stats():
    # Установим маленький лимит истории
    reset_bus()
    core.events.event_bus._max_history = 3

    # Публикуем 5 событий
    for i in range(5):
        core.events.event_bus.publish('TEXT_SUBMITTED', {'doc_id': f'd{i}', 'text': 'x'})

    # История должна быть усечена до последних 3
    assert len(core.events.event_bus._event_history) == 3

    stats = core.events.get_activity_stats()
    assert stats['total_events'] == 3
    assert stats['submissions'] == len(core.events.event_bus.monitoring_data.submissions)
    # last_activity должен соответствовать ts последнего события в истории
    assert stats['last_activity'] == core.events.event_bus._event_history[-1].ts
