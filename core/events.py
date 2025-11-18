"""
Система событий для реального времени.
Работает только с реальными событиями.
"""

from typing import Callable, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Event:
    """Событие в системе"""
    name: str
    ts: str
    payload: Dict[str, Any]


@dataclass
class MonitoringData:
    """Данные для мониторинга"""
    submissions: List[Dict] = field(default_factory=list)
    check_results: List[Dict] = field(default_factory=list)
    alerts: List[Dict] = field(default_factory=list)
    max_entries: int = 100
    
    def add_submission(self, data: Dict):
        self.submissions.insert(0, data)
        if len(self.submissions) > self.max_entries:
            self.submissions = self.submissions[:self.max_entries]
    
    def add_check_result(self, data: Dict):
        self.check_results.insert(0, data)
        if len(self.check_results) > self.max_entries:
            self.check_results = self.check_results[:self.max_entries]
    
    def add_alert(self, data: Dict):
        self.alerts.insert(0, data)
        if len(self.alerts) > self.max_entries:
            self.alerts = self.alerts[:self.max_entries]


class EventBus:
    """
    Шина событий для реактивного программирования.
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self._event_history: List[Event] = []
        self.monitoring_data = MonitoringData()
        self._max_history = 200
    
    def subscribe(self, event_name: str, handler: Callable[[Event], None]) -> None:
        """Подписаться на событие"""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(handler)
    
    def publish(self, event_name: str, payload: Dict[str, Any]) -> None:
        """Опубликовать событие"""
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
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Error in event handler {handler.__name__}: {e}")
    
    def get_history(self, event_name: str = None, limit: int = 50) -> List[Event]:
        """Получить историю событий"""
        history = self._event_history
        
        if event_name:
            history = [e for e in history if e.name == event_name]
        
        return history[-limit:]


# Глобальная шина событий
event_bus = EventBus()


# ===== ОБРАБОТЧИКИ СОБЫТИЙ =====

def handle_text_submitted(event: Event) -> None:
    """Обработчик загрузки текста"""
    submission_data = {
        'type': 'submission',
        'doc_id': event.payload.get('doc_id', 'unknown'),
        'title': event.payload.get('title', 'Без названия'),
        'user_id': event.payload.get('user_id', 'unknown'),
        'username': event.payload.get('username', 'Unknown'),
        'full_name': event.payload.get('full_name', 'Unknown'),
        'timestamp': event.ts,
        'text_length': len(event.payload.get('text', ''))
    }
    event_bus.monitoring_data.add_submission(submission_data)


def handle_check_done(event: Event) -> None:
    """Обработчик завершения проверки"""
    similarity = event.payload.get('similarity', 0)
    
    check_data = {
        'type': 'check_result',
        'doc_id': event.payload.get('doc_id', 'unknown'),
        'doc_title': event.payload.get('doc_title', 'Без названия'),
        'author_username': event.payload.get('author_username', 'Unknown'),
        'author_full_name': event.payload.get('author_full_name', 'Unknown'),
        'similarity': similarity,
        'admin_id': event.payload.get('admin_id', 'unknown'),
        'admin_name': event.payload.get('admin_name', 'Unknown'),
        'timestamp': event.ts,
        'status': 'high' if similarity > 0.7 else 'medium' if similarity > 0.3 else 'low'
    }
    event_bus.monitoring_data.add_check_result(check_data)
    
    # Если высокая схожесть - создаем алерт
    if similarity > 0.7:
        alert_data = {
            'type': 'alert',
            'doc_id': event.payload.get('doc_id', 'unknown'),
            'doc_title': event.payload.get('doc_title', 'Без названия'),
            'author_username': event.payload.get('author_username', 'Unknown'),
            'author_full_name': event.payload.get('author_full_name', 'Unknown'),
            'similarity': similarity,
            'severity': 'high' if similarity > 0.9 else 'medium',
            'message': f'Обнаружено подозрительное совпадение: {round(similarity * 100)}%',
            'timestamp': event.ts,
            'requires_attention': True
        }
        event_bus.monitoring_data.add_alert(alert_data)


def handle_alert(event: Event) -> None:
    """Обработчик критических событий"""
    alert_data = {
        'type': 'alert',
        'doc_id': event.payload.get('doc_id', 'unknown'),
        'doc_title': event.payload.get('doc_title', 'Без названия'),
        'author_username': event.payload.get('author_username', 'Unknown'),
        'author_full_name': event.payload.get('author_full_name', 'Unknown'),
        'similarity': event.payload.get('similarity', 0),
        'severity': event.payload.get('severity', 'medium'),
        'message': event.payload.get('message', 'Неизвестное событие'),
        'timestamp': event.ts,
        'requires_attention': event.payload.get('similarity', 0) > 0.8
    }
    event_bus.monitoring_data.add_alert(alert_data)


# Регистрация обработчиков
def setup_event_handlers():
    """Инициализация обработчиков событий"""
    event_bus.subscribe('TEXT_SUBMITTED', handle_text_submitted)
    event_bus.subscribe('CHECK_DONE', handle_check_done)
    event_bus.subscribe('ALERT', handle_alert)


# ===== ВИТРИНЫ (VIEWS) =====

def get_recent_submissions(limit: int = 10) -> List[Dict]:
    """Витрина: последние загруженные тексты"""
    return event_bus.monitoring_data.submissions[:limit]


def get_check_results(limit: int = 20) -> List[Dict]:
    """Витрина: результаты проверок"""
    return event_bus.monitoring_data.check_results[:limit]


def get_suspicious_matches(threshold: float = 0.7) -> List[Dict]:
    """Витрина: подозрительные совпадения"""
    # Берем из check_results с высокой схожестью
    suspicious_checks = [
        check for check in event_bus.monitoring_data.check_results
        if check.get('similarity', 0) >= threshold
    ]
    
    # Добавляем алерты
    all_suspicious = suspicious_checks + event_bus.monitoring_data.alerts
    
    # Убираем дубликаты по doc_id и сортируем по времени
    seen_docs = set()
    unique_suspicious = []
    
    for item in all_suspicious:
        doc_id = item.get('doc_id')
        if doc_id not in seen_docs:
            seen_docs.add(doc_id)
            unique_suspicious.append(item)
    
    # Сортируем по времени (новые сначала)
    unique_suspicious.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return unique_suspicious[:20]


def get_activity_stats() -> Dict:
    """Статистика активности системы"""
    total_events = len(event_bus._event_history)
    
    return {
        'total_events': total_events,
        'submissions': len(event_bus.monitoring_data.submissions),
        'checks': len(event_bus.monitoring_data.check_results),
        'alerts': len(event_bus.monitoring_data.alerts),
        'last_activity': event_bus._event_history[-1].ts if event_bus._event_history else None
    }


# Инициализация обработчиков
setup_event_handlers()
