import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "legal_platform")

_client = None
_db = None


def get_mongo_client() -> MongoClient:
    """Returns a cached MongoDB client singleton."""
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URI)
    return _client


def get_db():
    """Returns the MongoDB database instance."""
    global _db
    if _db is None:
        client = get_mongo_client()
        _db = client[MONGODB_DB_NAME]
    return _db
