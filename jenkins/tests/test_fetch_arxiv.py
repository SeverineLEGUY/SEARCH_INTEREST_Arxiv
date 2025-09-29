import os
import pytest
from unittest.mock import patch, MagicMock
from jenkins.tests.fetch_arxiv_unitaire import fetch_arxiv, push_to_s3

# Exemple de configuration : récupérer des articles pour 2 jours
TEST_QUERY = "machine learning"
MAX_RESULTS = 5
TEST_OUTPUT_FILE = "data/output_data.csv"


@pytest.fixture
def mock_s3_upload():
    with patch("jenkins.tests.fetch_arxiv_unitaire.push_to_s3") as mock_upload:
        yield mock_upload


@pytest.fixture
def mock_fetch_arxiv_response():
    # Simule une réponse simplifiée de fetch_arxiv
    sample_data = [
        {"id": "1234.5678", "title": "Test Paper 1", "summary": "Résumé 1"},
        {"id": "2345.6789", "title": "Test Paper 2", "summary": "Résumé 2"},
    ]
    with patch("jenkins.tests.fetch_arxiv_unitaire.fetch_arxiv", return_value=sample_data) as mock_fetch:
        yield mock_fetch


def test_fetch_arxiv_returns_list(mock_fetch_arxiv_response):
    results = fetch_arxiv(TEST_QUERY, max_results=MAX_RESULTS)
    assert isinstance(results, list)
    assert len(results) <= MAX_RESULTS
    assert "id" in results[0]
    assert "title" in results[0]
    assert "summary" in results[0]


def test_push_to_s3_called(mock_fetch_arxiv_response, mock_s3_upload):
    # Appelle la fonction ETL simplifiée
    articles = fetch_arxiv(TEST_QUERY, max_results=MAX_RESULTS)
    push_to_s3(articles, bucket_name=os.getenv("S3_BUCKET_NAME", "test-bucket"), output_file=TEST_OUTPUT_FILE)
    
    # Vérifie que push_to_s3 a été appelé
    mock_s3_upload.assert_called_once()


def test_output_file_created(tmp_path, mock_fetch_arxiv_response, mock_s3_upload):
    # On redirige le fichier vers tmp_path pour test local
    test_file = tmp_path / "output_data.csv"
    articles = fetch_arxiv(TEST_QUERY, max_results=MAX_RESULTS)
    
    push_to_s3(articles, bucket_name="dummy-bucket", output_file=str(test_file))
    
    # Vérifie que le fichier a été créé
    assert test_file.exists()