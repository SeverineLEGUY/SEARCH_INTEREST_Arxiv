# test_fetch_arxiv.py
import pytest
from unittest.mock import patch, MagicMock
import json
from fetch_arxiv import fetch_arxiv, push_to_redis, get_redis_client

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

# === TEST 1: Fetch Arxiv - Basic Validations ===
@patch("fetch_arxiv.feedparser.parse")
def test_fetch_arxiv_valid_data(mock_parse):
    # Mock du feedparser
    mock_parse.return_value.entries = [make_mock_entry()]
    
    # Simuler le contexte Airflow pour push dans XCom
    mock_context = {'ti': MagicMock()}
    
    fetch_arxiv(**mock_context)
    
    # Récupérer la valeur passée à xcom_push
    publications = mock_context['ti'].xcom_push.call_args[1]['value']
    
    assert isinstance(publications, list)
    assert len(publications) > 0
    
    pub = publications[0]
    assert isinstance(pub["id"], str)
    assert isinstance(pub["title"], str)
    assert isinstance(pub["summary"], str)
    assert isinstance(pub["published"], str)
    assert isinstance(pub["link"], str)
    assert isinstance(pub["authors"], list)
    assert all(isinstance(author, str) for author in pub["authors"])
    assert len(publications) <= 10

# === TEST 2: Vérification liste appendée ===
@patch("fetch_arxiv.feedparser.parse")
def test_fetch_arxiv_append_works(mock_parse):
    mock_parse.return_value.entries = [make_mock_entry(), make_mock_entry()]
    mock_context = {'ti': MagicMock()}
    
    fetch_arxiv(**mock_context)
    
    publications = mock_context['ti'].xcom_push.call_args[1]['value']
    assert len(publications) == 2

# === TEST 3: Push Redis - Connexion et Envoi ===
@patch("fetch_arxiv.redis.Redis")
def test_push_to_redis_connection_and_data(mock_redis_class):
    mock_redis_instance = MagicMock()
    mock_redis_class.return_value = mock_redis_instance
    
    # Simuler XCom
    mock_context = {'ti': MagicMock()}
    mock_context['ti'].xcom_pull.return_value = [{
        "id": "1234",
        "title": "Test Title",
        "summary": "Summary",
        "published": "2025-01-01T10:00:00Z",
        "link": "http://arxiv.org/abs/1234",
        "authors": ["Author One", "Author Two"],
        "updated": "2025-01-01T10:00:00Z",
        "category": "cs.AI"
    }]
    
    push_to_redis(**mock_context)
    
    # Vérifier que rpush a été appelé
    assert mock_redis_instance.rpush.called