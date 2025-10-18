"""
Функциональные типы Maybe и Either для безопасной обработки ошибок
"""

from typing import TypeVar, Generic, Callable, Union, Tuple
from core.domain import Document

T = TypeVar('T')
E = TypeVar('E')
R = TypeVar('R')


def validate_submission(text: str, min_length: int = 10) -> Either[str, str]:
    """
    Валидация текста перед проверкой.
    Возвращает Either: Left с ошибкой или Right с валидным текстом.
    
    Args:
        text: Текст для валидации
        min_length: Минимальная длина текста
        
    Returns:
        Either[str, str]
        
    Example:
        result = validate_submission(text, 50)
        if result.is_right():
            valid_text = result.get_right()
            # проверяем текст
        else:
            error = result.get_left()
            print(f"Ошибка: {error}")
    """
    if not text or not text.strip():
        return Either.left("Текст не может быть пустым")
    
    if len(text) < min_length:
        return Either.left(f"Текст слишком короткий (минимум {min_length} символов)")
    
    if len(text) > 100000:
        return Either.left("Текст слишком длинный (максимум 100000 символов)")
    
    return Either.right(text)

