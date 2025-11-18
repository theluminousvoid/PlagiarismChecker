import pytest
from core.lazy import paginate_documents, search_documents, progressive_check, filter_documents, batch_process
from core.domain import Document

# --------------------------
# Пагинация
# --------------------------
def test_paginate_documents_basic():
    docs = tuple(Document(id=f"d{i}", title=f"Doc {i}", text="text", author="Author", ts="2025-11-18T12:00:00Z") for i in range(15))
    page0 = list(paginate_documents(docs, page_size=5, page=0))
    page2 = list(paginate_documents(docs, page_size=5, page=2))

    assert len(page0) == 5
    assert page0[0].id == "d0"
    assert len(page2) == 5
    assert page2[0].id == "d10"

def test_paginate_documents_out_of_range():
    docs = tuple(Document(id=f"d{i}", title=f"Doc {i}", text="text", author="Author", ts="ts") for i in range(3))
    page1 = list(paginate_documents(docs, page_size=5, page=1))
    assert page1 == []

# --------------------------
# Поиск документов
# --------------------------
def test_search_documents_title_author_text():
    docs = (
        Document(id="d1", title="Hello World", text="Some text here", author="Alice", ts="ts"),
        Document(id="d2", title="Python", text="Hello Alice", author="Bob", ts="ts")
    )

    results = list(search_documents(docs, "hello"))
    assert len(results) == 2
    assert results[0][1] > 0  # relevance > 0

def test_search_documents_empty_query():
    docs = (Document(id="d1", title="Hello", text="Text", author="A", ts="ts"),)
    results = list(search_documents(docs, ""))
    assert results == []

# --------------------------
# Progressive check
# --------------------------
def test_progressive_check_basic(monkeypatch):
    # Подменим normalize, tokenize, ngrams, jaccard для простого контроля
    monkeypatch.setattr("core.lazy.normalize", lambda x: x.lower())
    monkeypatch.setattr("core.lazy.tokenize", lambda x: x.split())
    monkeypatch.setattr("core.lazy.ngrams", lambda tokens, n: [tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1)] if len(tokens)>=n else [tuple(tokens)])
    monkeypatch.setattr("core.lazy.jaccard", lambda a, b: 1.0 if a==b else 0.0)

    docs = (
        Document(id="d1", title="Doc1", text="Hello world", author="Alice", ts="ts"),
        Document(id="d2", title="Doc2", text="Python rocks", author="Bob", ts="ts")
    )

    results = list(progressive_check("Hello world", docs, n=2, min_similarity=0.5))
    assert len(results) == 1
    assert results[0]['doc_id'] == "d1"
    assert results[0]['similarity'] == 1.0
    assert results[0]['progress'] == 50.0

# --------------------------
# Filter documents
# --------------------------
def test_filter_documents_basic():
    docs = (
        Document(id="d1", title="Doc1", text="text", author="Alice", ts="ts"),
        Document(id="d2", title="Doc2", text="text", author="Bob", ts="ts")
    )
    filtered = list(filter_documents(docs, lambda d: d.author=="Alice"))
    assert len(filtered) == 1
    assert filtered[0].author == "Alice"

# --------------------------
# Batch processing
# --------------------------
def test_batch_process_basic():
    items = tuple(range(12))
    batches = list(batch_process(items, batch_size=5))
    assert len(batches) == 3
    assert batches[0] == (0,1,2,3,4)
    assert batches[-1] == (10,11)
