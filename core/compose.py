"""
Композиция функций и пайплайны.
Лаба №4: Функциональные паттерны
"""
from typing import Callable, Any, TypeVar
from functools import reduce
from core.domain import Document, Submission
from core.transforms import normalize, tokenize, ngrams
from core.ftypes import Maybe, Either

T = TypeVar('T')
U = TypeVar('U')
V = TypeVar('V')


def compose(*functions: Callable) -> Callable:
    """
    Композиция функций справа налево: compose(f, g, h)(x) = f(g(h(x)))
    
    Пример:
        process = compose(
            lambda x: x * 2,
            lambda x: x + 1,
            lambda x: x ** 2
        )
        result = process(3)  # ((3**2) + 1) * 2 = 20
    """
    def composed(x):
        return reduce(lambda acc, f: f(acc), reversed(functions), x)
    return composed


def pipe(*functions: Callable) -> Callable:
    """
    Композиция функций слева направо: pipe(f, g, h)(x) = h(g(f(x)))
    Более интуитивная запись для последовательных операций.
    
    Пример:
        process = pipe(
            lambda x: x ** 2,      # 1. возводим в квадрат
            lambda x: x + 1,       # 2. прибавляем 1
            lambda x: x * 2        # 3. умножаем на 2
        )
        result = process(3)  # ((3**2) + 1) * 2 = 20
    """
    def piped(x):
        return reduce(lambda acc, f: f(acc), functions, x)
    return piped


def text_processing_pipeline(text: str, n: int = 3) -> tuple:
    """
    Полный пайплайн обработки текста.
    
    Пример:
        result = text_processing_pipeline("Привет, Мир!")
        # ("привет мир", ("привет", "мир"), (("привет", "мир"),))
    """
    process = pipe(
        normalize,
        tokenize,
        lambda tokens: ngrams(tokens, n)
    )
    
    normalized = normalize(text)
    tokens = tokenize(normalized)
    grams = ngrams(tokens, n)
    
    return (normalized, tokens, grams)


def safe_doc_pipeline(docs: tuple, doc_id: str) -> Maybe[Document]:
    """
    Безопасный пайплайн для получения документа.
    Использует Maybe для обработки отсутствия документа.
    
    Пример:
        doc = safe_doc_pipeline(documents, "doc_001")
        if doc.is_just():
            print(doc.get().title)
    """
    matching = tuple(filter(lambda d: d.id == doc_id, docs))
    if len(matching) > 0:
        return Maybe.just(matching[0])
    return Maybe.nothing()


def validate_submission(sub: Submission, min_length: int = 50) -> Either[str, Submission]:
    """
    Валидация проверки с использованием Either.
    
    Пример:
        result = validate_submission(submission, min_length=50)
        if result.is_right():
            print("Валидация пройдена")
        else:
            print(f"Ошибка: {result.get_left()}")
    """
    if not sub.text or len(sub.text.strip()) == 0:
        return Either.left("Текст не может быть пустым")
    
    if len(sub.text) < min_length:
        return Either.left(f"Текст слишком короткий (минимум {min_length} символов)")
    
    return Either.right(sub)


def process_submission_pipeline(sub: Submission, min_length: int = 50) -> Either[str, tuple]:
    """
    Полный пайплайн обработки проверки с валидацией.
    
    Пример:
        result = process_submission_pipeline(submission)
        if result.is_right():
            normalized, tokens, grams = result.get_right()
    """
    return (validate_submission(sub, min_length)
            .map(lambda s: s.text)
            .map(normalize)
            .map(tokenize)
            .map(lambda tokens: (normalize(sub.text), tokens, ngrams(tokens, 3))))


def map_documents(func: Callable[[Document], T], docs: tuple) -> tuple:
    """
    Функциональный map для документов.
    
    Пример:
        titles = map_documents(lambda d: d.title, documents)
        lengths = map_documents(lambda d: len(d.text), documents)
    """
    return tuple(map(func, docs))


def filter_documents(predicate: Callable[[Document], bool], docs: tuple) -> tuple:
    """
    Функциональный filter для документов.
    
    Пример:
        long_docs = filter_documents(lambda d: len(d.text) > 100, documents)
        knut_docs = filter_documents(lambda d: "Кнут" in d.author, documents)
    """
    return tuple(filter(predicate, docs))


def reduce_documents(func: Callable[[T, Document], T], docs: tuple, initial: T) -> T:
    """
    Функциональный reduce для документов.
    
    Пример:
        total_length = reduce_documents(
            lambda acc, doc: acc + len(doc.text),
            documents,
            0
        )
    """
    return reduce(func, docs, initial)


def chain(*functions: Callable[[Maybe], Maybe]) -> Callable[[Maybe], Maybe]:
    """
    Цепочка операций над Maybe.
    
    Пример:
        process = chain(
            lambda m: m.map(normalize),
            lambda m: m.map(tokenize),
            lambda m: m.filter(lambda t: len(t) > 0)
        )
    """
    def chained(maybe: Maybe) -> Maybe:
        return reduce(lambda acc, f: f(acc), functions, maybe)
    return chained


def try_parse_int(value: str) -> Either[str, int]:
    """
    Безопасное преобразование строки в число.
    
    Пример:
        result = try_parse_int("42")
        if result.is_right():
            print(result.get_right())  # 42
    """
    try:
        return Either.right(int(value))
    except ValueError:
        return Either.left(f"Не удалось преобразовать '{value}' в число")


def safe_divide(a: float, b: float) -> Either[str, float]:
    """
    Безопасное деление с обработкой деления на ноль.
    
    Пример:
        result = safe_divide(10, 2)
        if result.is_right():
            print(result.get_right())  # 5.0
    """
    if b == 0:
        return Either.left("Деление на ноль")
    return Either.right(a / b)


def sequence_maybe(maybes: tuple) -> Maybe[tuple]:
    """
    Преобразует кортеж Maybe в Maybe кортежа.
    Если хотя бы один Maybe.nothing(), возвращает Maybe.nothing()
    
    Пример:
        result = sequence_maybe((
            Maybe.just(1),
            Maybe.just(2),
            Maybe.just(3)
        ))
        # Maybe.just((1, 2, 3))
    """
    results = []
    for m in maybes:
        if m.is_nothing():
            return Maybe.nothing()
        results.append(m.get())
    return Maybe.just(tuple(results))


def sequence_either(eithers: tuple) -> Either[str, tuple]:
    """
    Преобразует кортеж Either в Either кортежа.
    Если хотя бы один Left, возвращает первый Left.
    
    Пример:
        result = sequence_either((
            Either.right(1),
            Either.right(2),
            Either.right(3)
        ))
        # Either.right((1, 2, 3))
    """
    results = []
    for e in eithers:
        if e.is_left():
            return Either.left(e.get_left())
        results.append(e.get_right())
    return Either.right(tuple(results))