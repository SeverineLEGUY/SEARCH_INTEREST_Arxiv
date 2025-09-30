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


# -----------------------------
# Fonction pour récupérer les données Arxiv
# -----------------------------
import os
import requests
import boto3
from datetime import datetime
import xml.etree.ElementTree as ET # <-- NOUVEL IMPORT
import csv # <-- NOUVEL IMPORT pour la sauvegarde locale

# ... (votre configuration)

# -----------------------------
# Fonction pour récupérer les données Arxiv (MODIFIÉE)
# -----------------------------
def fetch_arxiv(query="cat:cs.LG", max_results=5):
    """Récupère, parse et retourne les articles depuis l'API Arxiv."""
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
    xml_string = response.text # Votre code initial
    
    # --- LOGIQUE DE PARSING AJOUTÉE ---
    NS = {'atom': 'http://www.w3.org/2005/Atom'}
    articles = []
    
    try:
        root = ET.fromstring(xml_string)
        for entry in root.findall('atom:entry', NS):
            article = {
                'id': entry.find('atom:id', NS).text.split('/')[-1] if entry.find('atom:id', NS) is not None else 'N/A',
                'published': entry.find('atom:published', NS).text if entry.find('atom:published', NS) is not None else 'N/A',
                'title': entry.find('atom:title', NS).text.strip() if entry.find('atom:title', NS) is not None else 'N/A',
                'summary': entry.find('atom:summary', NS).text.strip() if entry.find('atom:summary', NS) is not None else 'N/A',
            }
            articles.append(article)
    except ET.ParseError as e:
        print(f"Erreur de parsing XML: {e}")
        return []
        
    return articles # ✅ (Résout 'test_fetch_arxiv_returns_list')

# -----------------------------
# Fonction pour uploader sur S3
# -----------------------------
def upload_to_s3(articles: list, filename=None): # <-- Type Hinting pour la clarté
    """Sauvegarde les articles localement et les upload sur S3."""
    if not all([S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY]):
        raise EnvironmentError("Il manque une variable d'environnement AWS ou S3_BUCKET.")

    if filename is None:
        filename = f"arxiv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv" # Changement d'extension
    
    # 1. SAUVEGARDE LOCALE DANS UN FICHIER TEMPORAIRE (NÉCESSAIRE pour le test d'existence)
    # Nous allons convertir la liste des dictionnaires en CSV
    if articles:
        # Assurez-vous d'avoir des en-têtes (clé du premier dictionnaire)
        fieldnames = articles[0].keys()
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(articles)
        except Exception as e:
            raise IOError(f"Erreur lors de la sauvegarde locale du fichier {filename}: {e}")

    # 2. Upload S3 (utilise le fichier local créé)
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    
    # Utiliser upload_file qui est plus adapté pour uploader un fichier local
    s3.upload_file(filename, S3_BUCKET, filename)
    
    print(f"✅ Fichier uploadé sur S3: s3://{S3_BUCKET}/{filename}") 
    # Le fichier existe maintenant localement et sur S3. ✅ (Résout 'test_output_file_created')

# ----------------------------
# run-etl-pipeline
# -----------------------------

def run_etl_pipeline(query="cat:cs.LG", max_results=5):
    """Exécute l'intégralité du pipeline ETL : fetch -> upload."""
    
    # 1. FETCH
    articles = fetch_arxiv(query, max_results) 
    
    if articles:
        # 2. UPLOAD
        upload_to_s3(articles) # upload_to_s3 utilise des valeurs par défaut pour le filename
        return True
    return False
# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    print("🔄 Récupération des articles Arxiv...")
    
    # 🚨 REMPLACEZ TOUTE LA LOGIQUE PAR L'APPEL À LA FONCTION PRINCIPALE
    success = run_etl_pipeline(max_results=10)
    
    if success:
        print("✅ ETL terminé avec succès.")
    else:
        print("❌ ETL terminé avec échec ou sans articles.")