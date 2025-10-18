"""
Неизменяемые модели данных для системы проверки оригинальности.
Все классы используют @dataclass(frozen=True) для иммутабельности.
"""
from dataclasses import dataclass
from typing import Dict, Any, Tuple


@dataclass(frozen=True)
class Document:
    """Эталонный документ в базе знаний"""
    id: str
    title: str
    text: str
    author: str
    ts: str  # timestamp в формате ISO


@dataclass(frozen=True)
class User:
    """Пользователь системы"""
    id: str
    name: str
    role: str = "user"  # "user" или "admin"


@dataclass(frozen=True)
class Submission:
    """Текст пользователя для проверки на плагиат"""
    id: str
    user_id: str
    text: str
    ts: str


@dataclass(frozen=True)
class Token:
    """Токен (слово) из документа"""
    id: str
    doc_id: str
    value: str


@dataclass(frozen=True)
class Ngram:
    """N-грамма (последовательность слов)"""
    id: str
    doc_id: str
    values: Tuple[str, ...]
    hash: int  # хэш для быстрого сравнения


@dataclass(frozen=True)
class CheckResult:
    """Результат проверки текста на плагиат"""
    id: str
    submission_id: str
    score: float  # 0.0 - 1.0 (процент похожести)
    matches: Tuple[str, ...]  # ID похожих документов
    details: Dict[str, float] = None  # детальная информация по каждому документу


@dataclass(frozen=True)
class Rule:
    """Правило проверки"""
    id: str
    kind: str  # "min_length", "similarity_threshold", "stopwords"
    payload: Dict[str, Any]


@dataclass(frozen=True)
class Event:
    """Событие в системе (для FRP)"""
    id: str
    ts: str
    name: str  # "TEXT_SUBMITTED", "CHECK_DONE", "ALERT"
    payload: Dict[str, Any]