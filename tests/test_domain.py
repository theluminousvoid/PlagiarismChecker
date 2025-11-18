import pytest
from core.domain import Document, User, Submission, Token, Ngram, CheckResult, Rule, Event

# --------------------------
# Document
# --------------------------
def test_document_creation():
    doc = Document(id="d1", title="Title", text="Some text", author="Alice", ts="2025-11-18T12:00:00Z")
    assert doc.id == "d1"
    assert doc.title == "Title"
    assert doc.text == "Some text"
    assert doc.author == "Alice"
    assert doc.ts == "2025-11-18T12:00:00Z"

def test_document_immutable():
    doc = Document(id="d1", title="Title", text="Some text", author="Alice", ts="ts")
    with pytest.raises(AttributeError):
        doc.title = "New Title"

# --------------------------
# User
# --------------------------
def test_user_defaults_and_custom_role():
    user1 = User(id="u1", name="Bob")
    assert user1.role == "user"

    user2 = User(id="u2", name="Admin", role="admin")
    assert user2.role == "admin"

# --------------------------
# Submission
# --------------------------
def test_submission_creation():
    sub = Submission(id="s1", user_id="u1", text="hello", ts="2025-11-18T12:00:00Z")
    assert sub.text == "hello"
    assert sub.user_id == "u1"

# --------------------------
# Token & Ngram
# --------------------------
def test_token_and_ngram_creation():
    token = Token(id="t1", doc_id="d1", value="word")
    assert token.value == "word"
    
    ngram = Ngram(id="n1", doc_id="d1", values=("word1", "word2"), hash=12345)
    assert ngram.values == ("word1", "word2")
    assert ngram.hash == 12345

# --------------------------
# CheckResult
# --------------------------
def test_checkresult_defaults():
    cr = CheckResult(id="c1", submission_id="s1", score=0.75, matches=("d1", "d2"))
    assert cr.score == 0.75
    assert cr.details is None

# --------------------------
# Rule
# --------------------------
def test_rule_creation():
    rule = Rule(id="r1", kind="min_length", payload={"min": 10})
    assert rule.kind == "min_length"
    assert rule.payload["min"] == 10

# --------------------------
# Event
# --------------------------
def test_event_creation():
    ev = Event(id="e1", ts="2025-11-18T12:00:00Z", name="TEXT_SUBMITTED", payload={"doc_id": "d1"})
    assert ev.name == "TEXT_SUBMITTED"
    assert ev.payload["doc_id"] == "d1"
