import os
import requests
import boto3
from datetime import datetime

# -----------------------------
# Configuration via variables d'environnement
# -----------------------------
S3_BUCKET = os.getenv("S3_BUCKET")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

if not all([S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY]):
    raise EnvironmentError("Il manque une variable d'environnement AWS ou S3_BUCKET.")

# -----------------------------
# Fonction pour récupérer les données Arxiv
# -----------------------------
def fetch_arxiv(query="cat:cs.LG", max_results=5):
    """Récupère les derniers articles depuis l'API Arxiv."""
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "lastUpdatedDate",
        "sortOrder": "descending"
    }
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    return response.text

# -----------------------------
# Fonction pour uploader sur S3
# -----------------------------
def upload_to_s3(content, filename=None):
    """Upload le contenu sur S3."""
    if filename is None:
        filename = f"arxiv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"

    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    s3.put_object(Bucket=S3_BUCKET, Key=filename, Body=content)
    print(f"✅ Fichier uploadé sur S3: s3://{S3_BUCKET}/{filename}")

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    print("🔄 Récupération des articles Arxiv...")
    data = fetch_arxiv(max_results=10)
    print(f"✅ Récupération terminée, {len(data)} caractères récupérés.")

    print("🔄 Upload sur S3...")
    upload_to_s3(data)
    print("✅ ETL terminé avec succès.")