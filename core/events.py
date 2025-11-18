"""
Система событий для реального времени.
Внутренний модуль - пользователь видит только результат работы.
"""

from typing import Callable, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
from functools import reduce


@dataclass(frozen=True)
class Event:
    """Событие в системе"""
    name: str
    ts: str
    payload: Dict[str, Any]


class EventBus:
    """
    Шина событий для реактивного программирования.
    Обеспечивает связь между компонентами через события.
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event, Dict], Dict]]] = {}
        self._event_history: List[Event] = []
        self._max_history = 100
    
    def subscribe(self, event_name: str, handler: Callable[[Event, Dict], Dict]) -> None:
        """
        Подписаться на событие.
        
        Args:
            event_name: Имя события (TEXT_SUBMITTED, CHECK_DONE, ALERT)
            handler: Чистая функция-обработчик
        """
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(handler)
    
    def publish(self, event_name: str, payload: Dict[str, Any]) -> List[Dict]:
        """
        Опубликовать событие.
        
        Args:
            event_name: Имя события
            payload: Данные события
            
        Returns:
            Список результатов от всех обработчиков
        """
        event = Event(
            name=event_name,
            ts=datetime.utcnow().isoformat() + 'Z',
            payload=payload
        )
        
        # Сохраняем в историю
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Вызываем подписчиков
        handlers = self._subscribers.get(event_name, [])
        
        # Используем функциональный подход: reduce для агрегации результатов
        def process_handler(results: List[Dict], handler: Callable) -> List[Dict]:
            try:
                result = handler(event, payload)
                return results + [result] if result else results
            except Exception as e:
                return results + [{'error': str(e)}]
        
        return reduce(process_handler, handlers, [])
    
    def get_history(self, event_name: str = None, limit: int = 50) -> List[Event]:
        """
        Получить историю событий.
        
        Args:
            event_name: Фильтр по имени события (опционально)
            limit: Максимальное количество событий
            
        Returns:
            Список событий
        """
        history = self._event_history
        
        if event_name:
            history = [e for e in history if e.name == event_name]
        
        return history[-limit:]
    
    def clear_history(self) -> None:
        """Очистить историю событий"""
        self._event_history = []


# Глобальная шина событий
event_bus = EventBus()


# ===== ОБРАБОТЧИКИ СОБЫТИЙ (ЧИСТЫЕ ФУНКЦИИ) =====

def handle_text_submitted(event: Event, payload: Dict) -> Dict:
    """
    Обработчик загрузки текста.
    Создаёт витрину "Новые тексты".
    """
    return {
        'type': 'new_submission',
        'user_id': payload.get('user_id'),
        'doc_id': payload.get('doc_id'),
        'title': payload.get('title'),
        'timestamp': event.ts,
        'text_length': len(payload.get('text', ''))
    }


def handle_check_done(event: Event, payload: Dict) -> Dict:
    """
    Обработчик завершения проверки.
    Обновляет витрину "Результаты проверок".
    """
    similarity = payload.get('similarity', 0)
    
    return {
        'type': 'check_result',
        'doc_id': payload.get('doc_id'),
        'similarity': similarity,
        'status': 'suspicious' if similarity > 0.7 else 'clear',
        'timestamp': event.ts,
        'checked_by': payload.get('admin_id')
    }


def handle_alert(event: Event, payload: Dict) -> Dict:
    """
    Обработчик критических событий.
    Создаёт оповещения о подозрительных совпадениях.
    """
    return {
        'type': 'alert',
        'severity': payload.get('severity', 'medium'),
        'message': payload.get('message'),
        'doc_id': payload.get('doc_id'),
        'similarity': payload.get('similarity'),
        'timestamp': event.ts,
        'requires_attention': payload.get('similarity', 0) > 0.8
    }


def handle_suspicious_pattern(event: Event, payload: Dict) -> Dict:
    """
    Обработчик обнаружения подозрительных паттернов.
    Анализирует активность пользователя.
    """
    return {
        'type': 'pattern_detected',
        'user_id': payload.get('user_id'),
        'pattern': payload.get('pattern'),
        'count': payload.get('count', 0),
        'timestamp': event.ts
    }


# Регистрация обработчиков
def setup_event_handlers():
    """Инициализация обработчиков событий"""
    event_bus.subscribe('TEXT_SUBMITTED', handle_text_submitted)
    event_bus.subscribe('CHECK_DONE', handle_check_done)
    event_bus.subscribe('ALERT', handle_alert)
    event_bus.subscribe('SUSPICIOUS_PATTERN', handle_suspicious_pattern)


# ===== ВИТРИНЫ (VIEWS) =====

def get_recent_submissions(limit: int = 10) -> List[Dict]:
    """
    Витрина: последние загруженные тексты.
    Используется для панели "Новые документы".
    """
    events = event_bus.get_history('TEXT_SUBMITTED', limit)
    
    return [
        {
            'doc_id': e.payload.get('doc_id'),
            'title': e.payload.get('title'),
            'user_id': e.payload.get('user_id'),
            'timestamp': e.ts,
            'text_length': len(e.payload.get('text', ''))
        }
        for e in events
    ]


def get_check_results(limit: int = 20) -> List[Dict]:
    """
    Витрина: результаты проверок.
    Используется для панели "Последние проверки".
    """
    events = event_bus.get_history('CHECK_DONE', limit)
    
    return [
        {
            'doc_id': e.payload.get('doc_id'),
            'similarity': e.payload.get('similarity', 0),
            'timestamp': e.ts,
            'admin_id': e.payload.get('admin_id')
        }
        for e in events
    ]


def get_suspicious_matches(threshold: float = 0.7) -> List[Dict]:
    """
    Витрина: подозрительные совпадения.
    Используется для панели "Требуют внимания".
    """
    check_events = event_bus.get_history('CHECK_DONE', 50)
    alert_events = event_bus.get_history('ALERT', 50)
    
    suspicious = []
    
    # Из проверок
    for e in check_events:
        similarity = e.payload.get('similarity', 0)
        if similarity >= threshold:
            suspicious.append({
                'doc_id': e.payload.get('doc_id'),
                'similarity': similarity,
                'timestamp': e.ts,
                'source': 'check'
            })
    
    # Из алертов
    for e in alert_events:
        if e.payload.get('requires_attention', False):
            suspicious.append({
                'doc_id': e.payload.get('doc_id'),
                'similarity': e.payload.get('similarity', 0),
                'message': e.payload.get('message'),
                'timestamp': e.ts,
                'source': 'alert'
            })
    
    # Сортируем по времени
    suspicious.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return suspicious[:20]


def get_activity_stats() -> Dict:
    """
    Статистика активности системы.
    Используется для dashboard.
    """
    all_events = event_bus.get_history(limit=100)
    
    return {
        'total_events': len(all_events),
        'submissions': len([e for e in all_events if e.name == 'TEXT_SUBMITTED']),
        'checks': len([e for e in all_events if e.name == 'CHECK_DONE']),
        'alerts': len([e for e in all_events if e.name == 'ALERT']),
        'last_activity': all_events[-1].ts if all_events else None
    }
