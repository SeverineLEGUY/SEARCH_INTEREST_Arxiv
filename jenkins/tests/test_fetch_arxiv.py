#vérifier la connexion
# vérifier qu'il y a des données
# vérifier si les données ont un bon type
#verifier en fonction de la longeur
#verifier qu'il y a bien la liste créée/appendé

import pytest
from unittest.mock import patch, MagicMock
import json
from arxiv_tasks import fetch_arxiv_publications_func, push_to_redis_func

# === MOCK ENTRY CONSTRUCTION ==
def make_mock_entry():
    mock_entry = MagicMock()
    mock_entry.id = "1234"
    mock_entry.title = "Test Title"
    mock_entry.summary = "Summary of the paper."
    mock_entry.published = "2025-01-01T10:00:00Z"
    mock_entry.link = "http://arxiv.org/abs/1234"
    mock_entry.authors = [MagicMock(name="Author One"), MagicMock(name="Author Two")]
    return mock_entry

# === TEST 1: Fetch Arxiv - Basic Validations ===
@patch("arxiv_tasks.feedparser.parse")
def test_fetch_arxiv_publications_func_valid_data(mock_parse):
    mock_parse.return_value.entries = [make_mock_entry()]

    publications = fetch_arxiv_publications_func()

    # Vérifier qu'on a bien une liste
    assert isinstance(publications, list)

    # Vérifier qu'il y a des données
    assert len(publications) > 0

    # Vérifier la structure des données
    pub = publications[0]
    assert isinstance(pub["id"], str)
    assert isinstance(pub["title"], str)
    assert isinstance(pub["summary"], str)
    assert isinstance(pub["published"], str)
    assert isinstance(pub["link"], str)
    assert isinstance(pub["authors"], list)
    assert all(isinstance(author, str) for author in pub["authors"])

    # Vérifier la longueur de la liste
    assert len(publications) <= 10

# === TEST 2: Vérification liste appendée ===
@patch("arxiv_tasks.feedparser.parse")
def test_fetch_arxiv_append_works(mock_parse):
    mock_parse.return_value.entries = [make_mock_entry(), make_mock_entry()]
    publications = fetch_arxiv_publications_func()

    # On s'attend à ce que les 2 entrées soient présentes
    assert len(publications) == 2

# === TEST 3: Push Redis - Connexion et Envoi ===
@patch("arxiv_tasks.redis.Redis")
def test_push_to_redis_func_connection_and_data(mock_redis_class):
    mock_redis_instance = MagicMock()
    mock_redis_class.return_value = mock_redis_instance

    publications = [{
        "id": "1234",
        "title": "Test Title",
        "summary": "Summary",
        "published": "2025-01-01T10:00:00Z",
        "link": "http://arxiv.org/abs/1234",
        "authors": ["Author One", "Author Two"]
    }]