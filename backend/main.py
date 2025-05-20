from fastapi import FastAPI, HTTPException
from bson.objectid import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient

def get_mongo_collection():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["arxiv"]
    return db["summaries"]

app = FastAPI()
collection = get_mongo_collection()

def serialize_doc(doc):
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc

@app.get("/summaries")
def get_all_summaries():
    docs = list(collection.find().sort("published", -1))
    return [serialize_doc(d) for d in docs]

@app.get("/summaries/{doc_id}")
def get_summary(doc_id: str):
    try:
        doc = collection.find_one({"_id": ObjectId(doc_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID invalide")

    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    return serialize_doc(doc)
