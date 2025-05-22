import os

from airflow.models import Variable

# from dotenv import load_dotenv

# Load .env variables
# load_dotenv()

# --- Configuration ---
VARIABLE_KEYS = [
    "ARXIV_CATEGORY",
    "ARXIV_START_DATE",

    "REDIS_HOST",
    "REDIS_PORT",
    "REDIS_TRAINQ",
    "REDIS_CLASSQ",

    "MONGO_URI",
    "MONGO_DB",
    "MONGO_SUMMARIZE",
    "MONGO_CLASSIFIY",

    "MLFLOW_TRACKING_URI",

    "MISTRAL_API_KEY",
]


# --- Add Airflow Variables ---
def create_variables():
    for key in VARIABLE_KEYS:
        val = os.getenv(key)
        if val is not None:
            Variable.set(key, val)
            print(f"[✓] Set Airflow Variable: {key}")
        else:
            print(f"[!] Skipped {key} — not found in .env")


# --- Run Import ---
if __name__ == "__main__":
    print("Importing .env to Airflow...")
    create_variables()
    print("Done.")
