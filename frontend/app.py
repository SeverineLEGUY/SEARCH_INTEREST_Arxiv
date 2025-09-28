import streamlit as st
import pymongo 
import pandas as pd 


st.title("DASHBOARD ARXIV")
st.write("Visualisation des articles résumés")



# Connexion MongoDB
client = pymongo.MongoClient("mongodb://backend-run-mongodb:27017/")
db = client["arxiv"]
collection = db["arxiv_summaries"]

# Chargement des données
#@st.cache_data
def load_data():
    data = list(collection.find({}, {"_id": 0}))
    return pd.DataFrame(data)

# Chargement
df = load_data()

# Titre principal
#st.title("📊 Dashboard ArXiv - Traitement automatique")

# ✅ Nombre total d'articles
st.metric("Nombre d’articles traités", len(df))

# Debug rapide (peut être supprimé)
st.write("🧪 Données brutes")
st.write(df)



# ✅ Diagramme par domaine
if "category" in df.columns:
    st.subheader("📚 Articles par domaine")
    st.bar_chart(df["category"].value_counts())

# ✅ Sélection d'un article par doc_id
if not df.empty and "id" in df.columns:
    selected_id = st.selectbox("Sélectionnez un `doc_id`", df["id"].dropna().unique())

    article = df[df["id"] == selected_id].iloc[0]

    # Détails
    st.subheader("🧾 Détails de l'article")
    st.write(f"**Titre :** {article.get('title')}")
    st.write(f"**Auteurs :** {', '.join(article.get('authors', []))}")
    st.write(f"**Domaine :** {article.get('category')}")
    st.write(f"**Date :** {article.get('published')}")
    st.markdown(f"[🔗 Lien vers arXiv]({article.get('link')})")

    # Résumés
    st.subheader("📄 Résumé original (EN)")
    st.write(article.get("summary", "Non disponible."))

    st.subheader("📄 Résumé en français 🇫🇷")
    st.write(article.get("summary_fr", "Résumé non encore généré."))
else:
    st.warning("Aucun article trouvé ou champ `doc_id` manquant.")

