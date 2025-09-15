"""
Модели данных - это "шаблоны" наших объектов.
@dataclass(frozen=True) означает, что объект НЕЛЬЗЯ изменить после создания.
Это называется "иммутабельность" (неизменяемость).
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)  # frozen=True делает объект неизменяемым
class Document:
    """Документ из базы знаний"""
    id: str          # уникальный номер
    title: str       # название
    text: str        # содержимое
    author: str      # автор
    ts: str          # время создания


@dataclass(frozen=True)
class User:
    """Пользователь системы"""
    id: str
    name: str


@dataclass(frozen=True)
class Submission:
    """Текст, который проверяет пользователь"""
    id: str
    user_id: str     # кто проверяет
    text: str        # что проверяем
    ts: str          # когда проверили


@dataclass(frozen=True)
class Rule:
    """Правило проверки"""
    id: str
    kind: str                    # тип правила (min_length, threshold)
    payload: Dict[str, Any]      # параметры правила
