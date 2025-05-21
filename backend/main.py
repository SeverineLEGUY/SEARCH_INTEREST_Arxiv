import os

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

from bson.objectid import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient

MONGO_URI = "mongodb://backend-run-mongodb:27017/"
MONGO_DB = "arxiv"
MONGO_COLLECTION = "summaries"

def get_mongo_collection():
    client = MongoClient("mongodb://backend-run-mongodb:27017/")
    db = client["arxiv"]
    return db["summaries"]

def serialize_doc(doc):
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc

@asynccontextmanager
async def session_context(app: FastAPI):
    """
    Async context manager for FastAPI's lifespan event.
    Initializes and cleans up resources like clients and models.
    """
    
    mongo_uri = os.getenv("MONGO_URI", MONGO_URI)
    mongo_db = os.getenv("MONGO_DB", MONGO_DB)
    mongo_collection = os.getenv("MONGO_COLLECTION", MONGO_COLLECTION)

    app.state.collection = get_mongo_collection()

    # 
    yield
    # Clean up resources here

app = FastAPI(lifespan=session_context)

@app.get("/")
async def root_endpoint():
    """Redirects the root path ('/') to the API documentation ('/docs')."""
    return RedirectResponse(url="/docs", status_code=308)

@app.get("/summaries")
async def get_all_summaries():
    docs = list(app.state.collection.find().sort("published", -1))
    return [serialize_doc(d) for d in docs]

@app.get("/summaries/{doc_id}")
async def get_summary(doc_id: str):
    try:
        doc = app.state.collection.find_one({"_id": ObjectId(doc_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID invalide")

    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    return serialize_doc(doc)
