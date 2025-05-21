import os
from contextlib import asynccontextmanager

from bson.errors import InvalidId
from bson.objectid import ObjectId
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pymongo import MongoClient

MONGO_URI = "mongodb://backend-run-mongodb:27017/"
MONGO_DB = "arxiv"
MONGO_SUMMARIZE = "arxiv_summaries"
MONGO_CLASSIFIY = "arxiv_classification"


def get_mongo_collection(mongo_uri: str, mongo_db: str, mongo_collection: str):
    client = MongoClient(mongo_uri)
    db = client[mongo_db]
    return db[mongo_collection]


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
    mongo_summarize = os.getenv("MONGO_SUMMARIZE", MONGO_SUMMARIZE)
    mongo_classify = os.getenv("MONGO_CLASSIFIY", MONGO_CLASSIFIY)

    app.state.summarize = get_mongo_collection(mongo_uri, mongo_db, mongo_summarize)
    app.state.classify = get_mongo_collection(mongo_uri, mongo_db, mongo_classify)

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
    docs = list(app.state.summarize.find().sort("published", -1))
    return [serialize_doc(d) for d in docs]


@app.get("/summaries/{doc_id}")
async def get_summary(doc_id: str):
    try:
        doc = app.state.summarize.find_one({"_id": ObjectId(doc_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID invalide")

    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    return serialize_doc(doc)


@app.get("/classifications")
async def get_all_classifications():
    docs = list(app.state.classify.find().sort("published", -1))
    return [serialize_doc(d) for d in docs]


@app.get("/classifications/{doc_id}")
async def get_classification(doc_id: str):
    try:
        doc = app.state.classify.find_one({"_id": ObjectId(doc_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID invalide")

    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    return serialize_doc(doc)
