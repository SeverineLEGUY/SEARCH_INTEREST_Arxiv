import boto3
import sys
import os

# Vérifie que le script a reçu les arguments nécessaires
if len(sys.argv) != 3:
    print("Usage: python upload_s3.py <bucket_name> <local_file_path>")
    sys.exit(1)

# Récupération des arguments passés par Jenkins
bucket_name = sys.argv[1]
file_path = sys.argv[2] # Le chemin local (ex: data/output_data.csv)

# L'objet S3 Key sera le nom du fichier (ex: output_data.csv)
s3_key = os.path.basename(file_path) 

# Initialisation du client S3 (utilise les variables d'environnement AWS_ACCESS_KEY_ID et AWS_SECRET_ACCESS_KEY)
s3_client = boto3.client("s3")

# Upload du fichier
try:
    # On utilise file_path (le chemin complet) pour l'upload
    s3_client.upload_file(file_path, bucket_name, s3_key)
    print(
        f"✅ Fichier '{file_path}' envoyé avec succès sur 's3://{bucket_name}/{s3_key}'"
    )
except Exception as e:
    print(f"❌ Erreur lors de l'upload sur S3 : {e}")