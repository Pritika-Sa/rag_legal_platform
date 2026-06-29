from database.connection import get_db


def init_db():
    """Initializes MongoDB collections and creates indexes."""
    db = get_db()

    db.documents.create_index("name", unique=True)
    db.documents.create_index("hash")

    db.clauses.create_index("doc_id")
    db.clauses.create_index([("doc_id", 1), ("section_name", 1)])

    db.contradictions.create_index("doc_id")

    db.clause_versions.create_index("clause_id")

    db.audit_logs.create_index("timestamp")

    db.counters.update_one(
        {"_id": "documents"}, {"$setOnInsert": {"seq": 0}}, upsert=True
    )
    db.counters.update_one(
        {"_id": "clauses"}, {"$setOnInsert": {"seq": 0}}, upsert=True
    )
    db.counters.update_one(
        {"_id": "contradictions"}, {"$setOnInsert": {"seq": 0}}, upsert=True
    )
    db.counters.update_one(
        {"_id": "clause_versions"}, {"$setOnInsert": {"seq": 0}}, upsert=True
    )
    db.counters.update_one(
        {"_id": "audit_logs"}, {"$setOnInsert": {"seq": 0}}, upsert=True
    )

    print("MongoDB collections and indexes initialized successfully.")


def _get_next_id(collection_name: str) -> int:
    """Auto-increment helper — returns the next integer ID for a collection."""
    db = get_db()
    result = db.counters.find_one_and_update(
        {"_id": collection_name},
        {"$inc": {"seq": 1}},
        return_document=True,
    )
    return result["seq"]


if __name__ == "__main__":
    init_db()
