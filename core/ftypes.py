"""
Функциональные типы Maybe и Either для безопасной обработки ошибок
Функциональные паттерны: Maybe/Either
Методы: 
        just(value) -	Создаёт контейнер с данными	| value
        nothing() -  Создаёт "пустой" контейнер	| None
        is_just() / is_nothing()  -	Проверяет, есть ли значение	| value is not None
        get(default) -	Возвращает значение или default	| value or default
        map(func) -	Применяет функцию, если значение есть |	list comprehension
        flat_map(func) -	То же, но если func возвращает | Maybe	"чистая композиция"
        filter(pred) -	Оставляет значение, если предикат | True	if condition:
        or_else(default) -	Возвращает значение или | default	value or default
"""

from typing import TypeVar, Generic, Callable, Union, Tuple
from core.domain import Document

T = TypeVar('T')
E = TypeVar('E')
R = TypeVar('R')


class Maybe(Generic[T]):
    """
    Maybe тип для безопасной обработки отсутствующих значений.
    Альтернатива None с явной семантикой.
    """
    
    def __init__(self, value: T = None, is_nothing: bool = False):
        self._value = value
        self._is_nothing = is_nothing
    
    @staticmethod
    def just(value: T) -> 'Maybe[T]':
        """Создать Maybe со значением"""
        return Maybe(value, False)
    
    @staticmethod
    def nothing() -> 'Maybe[T]':
        """Создать пустой Maybe"""
        return Maybe(None, True)
    
    def is_just(self) -> bool:
        """Проверить, есть ли значение"""
        return not self._is_nothing
    
    def is_nothing(self) -> bool:
        """Проверить, пустой ли Maybe"""
        return self._is_nothing
    
    def get(self, default: T = None) -> T:
        """Получить значение или default"""
        return self._value if not self._is_nothing else default
    
    def map(self, func: Callable[[T], R]) -> 'Maybe[R]':
        """
        Применить функцию к значению, если оно есть.
        
        Example:
            maybe_doc = Maybe.just(document)
            maybe_title = maybe_doc.map(lambda d: d.title)
        """
        if self._is_nothing:
            return Maybe.nothing()
        try:
            return Maybe.just(func(self._value))
        except Exception:
            return Maybe.nothing()
    
    def flat_map(self, func: Callable[[T], 'Maybe[R]']) -> 'Maybe[R]':
        """Применить функцию, возвращающую Maybe"""
        if self._is_nothing:
            return Maybe.nothing()
        return func(self._value)
    
    def filter(self, predicate: Callable[[T], bool]) -> 'Maybe[T]':
        """Фильтровать значение по предикату"""
        if self._is_nothing or not predicate(self._value):
            return Maybe.nothing()
        return self
    
    def or_else(self, default: T) -> T:
        """Получить значение или default"""
        return self._value if not self._is_nothing else default


class Either(Generic[E, R]):
    """
    Either тип для явной обработки ошибок без исключений.
    Left - ошибка, Right - успешный результат.
    """
    
    def __init__(self, value: Union[E, R], is_left: bool):
        self._value = value
        self._is_left = is_left
    
    @staticmethod
    def left(error: E) -> 'Either[E, R]':
        """Создать Either с ошибкой"""
        return Either(error, True)
    
    @staticmethod
    def right(value: R) -> 'Either[E, R]':
        """Создать Either с успешным значением"""
        return Either(value, False)
    
    def is_left(self) -> bool:
        """Это ошибка?"""
        return self._is_left
    
    def is_right(self) -> bool:
        """Это успешное значение?"""
        return not self._is_left
    
    def get_left(self, default: E = None) -> E:
        """Получить ошибку или default"""
        return self._value if self._is_left else default
    
    def get_right(self, default: R = None) -> R:
        """Получить значение или default"""
        return self._value if not self._is_left else default
    
    def map(self, func: Callable[[R], T]) -> 'Either[E, T]':
        """
        Применить функцию к значению, если это Right.
        
        Example:
            result = Either.right(5)
            doubled = result.map(lambda x: x * 2)  # Either.right(10)
        """
        if self._is_left:
            return Either.left(self._value)
        try:
            return Either.right(func(self._value))
        except Exception as e:
            return Either.left(str(e))
    
    def flat_map(self, func: Callable[[R], 'Either[E, T]']) -> 'Either[E, T]':
        """Применить функцию, возвращающую Either"""
        if self._is_left:
            return Either.left(self._value)
        return func(self._value)
    
    def map_left(self, func: Callable[[E], T]) -> 'Either[T, R]':
        """Применить функцию к ошибке"""
        if self._is_left:
            return Either.left(func(self._value))
        return Either.right(self._value)


# Утилиты для работы с документами

def safe_get_document(docs: Tuple[Document, ...], doc_id: str) -> Maybe[Document]:
    """
    Безопасное получение документа по ID.
    Возвращает Maybe вместо None.
    
    Args:
        docs: Кортеж документов
        doc_id: ID документа
        
    Returns:
        Maybe[Document]
        
    Example:
        result = safe_get_document(documents, "doc_001")
        if result.is_just():
            doc = result.get()
            print(doc.title)
        else:
            print("Документ не найден")
    """
    for doc in docs:
        if doc.id == doc_id:
            return Maybe.just(doc)
    return Maybe.nothing()


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


def validate_ngram_size(n: int) -> Either[str, int]:
    """
    Валидация размера n-грамм.
    
    Args:
        n: Размер n-грамм
        
    Returns:
        Either[str, int]
    """
    if n < 1:
        return Either.left("Размер n-грамм должен быть >= 1")
    if n > 10:
        return Either.left("Размер n-грамм слишком большой (максимум 10)")
    
    return Either.right(n)
