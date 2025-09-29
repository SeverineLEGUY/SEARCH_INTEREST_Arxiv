# test_fetch_arxiv.py
import pytest
from unittest.mock import patch, MagicMock
from airflow.models import Variable
from fetch_arxiv import fetch_arxiv, push_to_redis

# === MOCK ENTRY CONSTRUCTION ===
def make_mock_entry():
    mock_entry = MagicMock()
    mock_entry.id = "1234"
    mock_entry.title = "Test Title"
    mock_entry.summary = "Summary of the paper."
    mock_entry.updated = "2025-01-01T10:00:00Z"
    mock_entry.published = "2025-01-01T10:00:00Z"
    mock_entry.links = [MagicMock(href="http://arxiv.org/abs/1234", type="text/html")]
    mock_entry.authors = [MagicMock(name="Author One"), MagicMock(name="Author Two")]
    mock_entry.arxiv_primary_category = {'term': 'cs.AI'}
    return mock_entry

# === TEST 1: fetch_arxiv transforme bien les entries ===
@patch.object(Variable, "get", return_value="cs.AI")  # Évite KeyError
@patch("fetch_arxiv.feedparser.parse")
def test_fetch_arxiv_valid_data(mock_parse, mock_variable):
    mock_parse.return_value.entries = [make_mock_entry()]
    mock_context = {'ti': MagicMock()}
    
    fetch_arxiv(**mock_context)
    
    publications = mock_context['ti'].xcom_push.call_args[1]['value']
    assert isinstance(publications, list)
    assert len(publications) == 1
    pub = publications[0]
    assert pub["id"] == "1234"
    assert pub["title"] == "Test Title"
    assert pub["authors"] == ["Author One", "Author Two"]

# === TEST 2: fetch_arxiv avec plusieurs entrées ===
@patch.object(Variable, "get", return_value="cs.AI")
@patch("fetch_arxiv.feedparser.parse")
def test_fetch_arxiv_multiple_entries(mock_parse, mock_variable):
    mock_parse.return_value.entries = [make_mock_entry(), make_mock_entry()]
    mock_context = {'ti': MagicMock()}
    
    fetch_arxiv(**mock_context)
    
    publications = mock_context['ti'].xcom_push.call_args[1]['value']
    assert len(publications) == 2

# === TEST 3: push_to_redis appelle bien rpush ===
@patch("fetch_arxiv.redis.Redis")
def test_push_to_redis(mock_redis_class):
    mock_redis_instance = MagicMock()
    mock_redis_class.return_value = mock_redis_instance
    
    mock_context = {'ti': MagicMock()}
    mock_context['ti'].xcom_pull.return_value = [{"id": "1234", "title": "Test Title"}]
    
    push_to_redis(**mock_context)
    mock_redis_instance.rpush.assert_called()