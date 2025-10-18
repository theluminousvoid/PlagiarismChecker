import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.ftypes import (
    Maybe, Either, safe_get, safe_divide, 
    validate_positive, sequence_maybe
)


# ТЕСТЫ MAYBE
def test_maybe_just():
    m = Maybe.just(5)
    assert m.is_just()
    assert not m.is_nothing()
    assert m.get() == 5


def test_maybe_nothing():
    m = Maybe.nothing()
    assert m.is_nothing()
    assert not m.is_just()
    assert m.get() is None
    assert m.get(default=10) == 10


def test_maybe_map():
    m = Maybe.just(5)
    result = m.map(lambda x: x * 2)
    assert result.is_just()
    assert result.get() == 10
    
    # Map на Nothing
    n = Maybe.nothing()
    result = n.map(lambda x: x * 2)
    assert result.is_nothing()


def test_maybe_flat_map():
    m = Maybe.just(5)
    result = m.flat_map(lambda x: Maybe.just(x * 2))
    assert result.is_just()
    assert result.get() == 10
    
    # flat_map возвращает Nothing
    result = m.flat_map(lambda x: Maybe.nothing())
    assert result.is_nothing()


def test_maybe_filter():
    m = Maybe.just(5)
    
    # Предикат истинен
    result = m.filter(lambda x: x > 3)
    assert result.is_just()
    
    # Предикат ложен
    result = m.filter(lambda x: x > 10)
    assert result.is_nothing()


def test_maybe_or_else():
    m = Maybe.just(5)
    assert m.or_else(10) == 5
    
    n = Maybe.nothing()
    assert n.or_else(10) == 10


# ТЕСТЫ EITHER
def test_either_right():
    e = Either.right(5)
    assert e.is_right()
    assert not e.is_left()
    assert e.get_right() == 5


def test_either_left():
    e = Either.left("error")
    assert e.is_left()
    assert not e.is_right()
    assert e.get_left() == "error"


def test_either_map():
    e = Either.right(5)
    result = e.map(lambda x: x * 2)
    assert result.is_right()
    assert result.get_right() == 5.0


def test_either_error_propagation():
    # Ошибка должна пробрасываться через цепочку
    result = (Either.left("initial error")
              .map(lambda x: x * 2)
              .map(lambda x: x + 5))
    
    assert result.is_left()
    assert result.get_left() == "initial error" result.get_right() == 10
    
    # Map на Left
    err = Either.left("error")
    result = err.map(lambda x: x * 2)
    assert result.is_left()
    assert result.get_left() == "error"


def test_either_flat_map():
    e = Either.right(5)
    result = e.flat_map(lambda x: Either.right(x * 2))
    assert result.is_right()
    assert result.get_right() == 10
    
    # flat_map возвращает Left
    result = e.flat_map(lambda x: Either.left("error"))
    assert result.is_left()


def test_either_map_left():
    e = Either.left("error")
    result = e.map_left(lambda s: s.upper())
    assert result.is_left()
    assert result.get_left() == "ERROR"


def test_either_or_else():
    e = Either.right(5)
    assert e.or_else(10) == 5
    
    err = Either.left("error")
    assert err.or_else(10) == 10


# ТЕСТЫ ВСПОМОГАТЕЛЬНЫХ ФУНКЦИЙ
def test_safe_get():
    items = (1, 2, 3, 4, 5)
    
    # Валидный индекс
    result = safe_get(items, 2)
    assert result.is_just()
    assert result.get() == 3
    
    # Невалидный индекс
    result = safe_get(items, 10)
    assert result.is_nothing()


def test_safe_divide():
    # Нормальное деление
    result = safe_divide(10, 2)
    assert result.is_right()
    assert result.get_right() == 5.0
    
    # Деление на ноль
    result = safe_divide(10, 0)
    assert result.is_left()


def test_validate_positive():
    # Положительное число
    result = validate_positive(5)
    assert result.is_right()
    assert result.get_right() == 5
    
    # Отрицательное число
    result = validate_positive(-5)
    assert result.is_left()
    
    # Ноль
    result = validate_positive(0)
    assert result.is_left()


def test_sequence_maybe():
    # Все Just
    result = sequence_maybe((
        Maybe.just(1),
        Maybe.just(2),
        Maybe.just(3)
    ))
    assert result.is_just()
    assert result.get() == (1, 2, 3)
    
    # Есть Nothing
    result = sequence_maybe((
        Maybe.just(1),
        Maybe.nothing(),
        Maybe.just(3)
    ))
    assert result.is_nothing()
    
    # Пустой кортеж
    result = sequence_maybe(tuple())
    assert result.is_just()
    assert result.get() == tuple()


def test_maybe_chain():
    # Цепочка операций
    result = (Maybe.just("  HELLO  ")
              .map(str.strip)
              .map(str.lower)
              .map(lambda s: s + " world"))
    
    assert result.is_just()
    assert result.get() == "hello world"


def test_either_chain():
    # Цепочка операций с Either
    result = (Either.right(10)
              .map(lambda x: x * 2)
              .map(lambda x: x + 5)
              .map(lambda x: x / 5))
    
    assert result.is_right()
    assert