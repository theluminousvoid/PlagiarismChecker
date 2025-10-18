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
class Submission:
    """Текст пользователя для проверки на плагиат"""
    id: str
    user_id: str
    text: str
    ts: str
