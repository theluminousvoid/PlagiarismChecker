import pytest
from core.memo import check_submission_cached, clear_cache, get_cache_stats
from core.domain import Document, Submission

def test_check_submission_cached_basic(monkeypatch):
    # Подменим normalize, tokenize, ngrams, jaccard для контроля
    monkeypatch.setattr("core.memo.normalize", lambda x: x.lower())
    monkeypatch.setattr("core.memo.tokenize", lambda x: x.split())
    monkeypatch.setattr("core.memo.ngrams", lambda tokens, n: [tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1)] if len(tokens)>=n else [tuple(tokens)])
    monkeypatch.setattr("core.memo.jaccard", lambda a,b: 1.0 if a==b else 0.0)

    doc1 = Document(id="d1", title="Doc1", text="Hello world", author="Alice", ts="ts")
    doc2 = Document(id="d2", title="Doc2", text="Python rocks", author="Bob", ts="ts")
    submission = Submission(id="s1", user_id="u1", text="Hello world", ts="ts")

    clear_cache()
    result = check_submission_cached(submission, (doc1, doc2), n=2)

    # Проверяем топ-5 matches
    assert len(result['matches']) == 2
    assert result['score'] == 1.0
    assert result['matches'][0]['doc_id'] == "d1"

    # Статистика
    stats = result['stats']
    assert stats['documents_checked'] == 2
    assert stats['cache_used'] is True
    assert stats['tokens'] > 0
    assert stats['ngrams'] > 0

def test_cache_stats_reflects_hits_and_misses(monkeypatch):
    monkeypatch.setattr("core.memo.normalize", lambda x: x)
    monkeypatch.setattr("core.memo.tokenize", lambda x: x.split())
    monkeypatch.setattr("core.memo.ngrams", lambda tokens, n: [tuple(tokens)])
    monkeypatch.setattr("core.memo.jaccard", lambda a,b: 1.0 if a==b else 0.0)

    doc = Document(id="d1", title="Doc", text="abc", author="A", ts="ts")
    sub = Submission(id="s1", user_id="u1", text="abc", ts="ts")

    clear_cache()
    check_submission_cached(sub, (doc,))
    stats1 = get_cache_stats()
    check_submission_cached(sub, (doc,))
    stats2 = get_cache_stats()

    assert stats1['misses'] > 0
    assert stats2['hits'] > 0  # Вторая проверка должна использовать кэш

def test_clear_cache_resets_stats(monkeypatch):
    monkeypatch.setattr("core.memo.normalize", lambda x: x)
    monkeypatch.setattr("core.memo.tokenize", lambda x: x.split())
    monkeypatch.setattr("core.memo.ngrams", lambda tokens, n: [tuple(tokens)])
    monkeypatch.setattr("core.memo.jaccard", lambda a,b: 1.0 if a==b else 0.0)

    doc = Document(id="d1", title="Doc", text="abc", author="A", ts="ts")
    sub = Submission(id="s1", user_id="u1", text="abc", ts="ts")

    check_submission_cached(sub, (doc,))
    clear_cache()
    stats = get_cache_stats()
    assert stats['hits'] == 0
    assert stats['misses'] == 0
    assert stats['size'] == 0
