from datetime import datetime, timezone
from database.connection import get_db
from database.models import _get_next_id


def _now():
    return datetime.now(timezone.utc)


# ── Documents ──────────────────────────────────────────────────────────────

def add_document(name, path, file_hash):
    """Inserts a new document and returns its integer ID."""
    db = get_db()
    existing = db.documents.find_one({"name": name})
    if existing:
        return existing["id"]

    doc_id = _get_next_id("documents")
    db.documents.insert_one({
        "id": doc_id,
        "name": name,
        "path": path,
        "hash": file_hash,
        "upload_date": _now(),
    })
    add_audit_log("document_upload", f"Uploaded document '{name}' (ID: {doc_id})")
    return doc_id


def get_document_by_hash(file_hash):
    """Retrieves document by its hash."""
    db = get_db()
    return db.documents.find_one({"hash": file_hash})


def get_all_documents():
    """Retrieves all documents, newest first."""
    db = get_db()
    return list(db.documents.find().sort("upload_date", -1))


def get_document_by_id(doc_id):
    """Retrieves a document by ID."""
    db = get_db()
    return db.documents.find_one({"id": doc_id})


def delete_document(doc_id):
    """Deletes a document and all related data."""
    db = get_db()
    doc = db.documents.find_one({"id": doc_id})
    doc_name = doc["name"] if doc else f"ID {doc_id}"

    db.contradictions.delete_many({"doc_id": doc_id})
    clause_ids = [c["id"] for c in db.clauses.find({"doc_id": doc_id}, {"id": 1})]
    if clause_ids:
        db.clause_versions.delete_many({"clause_id": {"$in": clause_ids}})
    db.clauses.delete_many({"doc_id": doc_id})
    db.documents.delete_one({"id": doc_id})

    add_audit_log("document_delete", f"Deleted document '{doc_name}' (ID: {doc_id})")


# ── Clauses ────────────────────────────────────────────────────────────────

def add_clause(doc_id, section_name, text_content, page_num=None,
               classification=None, risk_category=None, risk_level="None",
               explanation=None, simplification=None):
    """Inserts a clause and returns its integer ID."""
    db = get_db()
    clause_id = _get_next_id("clauses")
    db.clauses.insert_one({
        "id": clause_id,
        "doc_id": doc_id,
        "section_name": section_name,
        "text_content": text_content,
        "page_num": page_num,
        "version": 1,
        "classification": classification,
        "risk_category": risk_category,
        "risk_level": risk_level,
        "explanation": explanation,
        "simplification": simplification,
    })
    return clause_id


def get_clauses_for_document(doc_id):
    """Retrieves all clauses for a document, ordered by ID."""
    db = get_db()
    return list(db.clauses.find({"doc_id": doc_id}).sort("id", 1))


def update_clause_text(clause_id, new_text, change_description="User manual update"):
    """Updates clause text, creates a version record, increments the version."""
    db = get_db()
    clause = db.clauses.find_one({"id": clause_id})
    if not clause:
        raise ValueError(f"Clause with ID {clause_id} not found.")

    old_text = clause["text_content"]
    old_version = clause["version"]
    new_version = old_version + 1

    version_id = _get_next_id("clause_versions")
    db.clause_versions.insert_one({
        "id": version_id,
        "clause_id": clause_id,
        "previous_text": old_text,
        "new_text": new_text,
        "change_description": change_description,
        "timestamp": _now(),
    })

    db.clauses.update_one(
        {"id": clause_id},
        {"$set": {"text_content": new_text, "version": new_version}},
    )

    add_audit_log(
        "clause_update",
        f"Updated clause ID {clause_id} ('{clause['section_name']}') in doc {clause['doc_id']} to V{new_version}",
    )
    return new_version


def get_clause_versions(clause_id):
    """Retrieves the complete modification history for a clause."""
    db = get_db()
    return list(db.clause_versions.find({"clause_id": clause_id}).sort("timestamp", -1))


# ── Contradictions ─────────────────────────────────────────────────────────

def add_contradiction(doc_id, clause_id_1, clause_id_2, explanation, severity="Medium"):
    """Inserts a detected contradiction."""
    db = get_db()
    c_id = _get_next_id("contradictions")
    db.contradictions.insert_one({
        "id": c_id,
        "doc_id": doc_id,
        "clause_id_1": clause_id_1,
        "clause_id_2": clause_id_2,
        "explanation": explanation,
        "severity": severity,
    })
    return c_id


def get_contradictions_for_document(doc_id):
    """Gets all contradictions in a document with clause details joined."""
    db = get_db()
    contradictions = list(db.contradictions.find({"doc_id": doc_id}))

    for c in contradictions:
        cl1 = db.clauses.find_one({"id": c["clause_id_1"]})
        cl2 = db.clauses.find_one({"id": c["clause_id_2"]})
        c["section_1"] = cl1["section_name"] if cl1 else ""
        c["text_1"] = cl1["text_content"] if cl1 else ""
        c["section_2"] = cl2["section_name"] if cl2 else ""
        c["text_2"] = cl2["text_content"] if cl2 else ""

    return contradictions


# ── Audit Logs ─────────────────────────────────────────────────────────────

def add_audit_log(action, details=None):
    """Inserts an event into the audit logs."""
    db = get_db()
    log_id = _get_next_id("audit_logs")
    db.audit_logs.insert_one({
        "id": log_id,
        "action": action,
        "details": details,
        "timestamp": _now(),
    })
    return log_id


def get_audit_logs(limit=50):
    """Gets recent logs."""
    db = get_db()
    return list(db.audit_logs.find().sort("timestamp", -1).limit(limit))


# ── Dashboard Metrics ──────────────────────────────────────────────────────

def get_dashboard_metrics(doc_id=None):
    """Aggregates metrics for the dashboard page."""
    db = get_db()

    if doc_id:
        total_clauses = db.clauses.count_documents({"doc_id": doc_id})
        total_contradictions = db.contradictions.count_documents({"doc_id": doc_id})
        risky_clauses = db.clauses.count_documents({
            "doc_id": doc_id,
            "risk_level": {"$in": ["High", "Medium"]},
        })

        pipeline = [
            {"$match": {"doc_id": doc_id}},
            {"$group": {"_id": "$risk_level", "count": {"$sum": 1}}},
        ]
        risk_dist = {r["_id"]: r["count"] for r in db.clauses.aggregate(pipeline)}
        total_documents = 1
    else:
        total_documents = db.documents.count_documents({})
        total_clauses = db.clauses.count_documents({})
        total_contradictions = db.contradictions.count_documents({})
        risky_clauses = db.clauses.count_documents({
            "risk_level": {"$in": ["High", "Medium"]},
        })

        pipeline = [
            {"$group": {"_id": "$risk_level", "count": {"$sum": 1}}},
        ]
        risk_dist = {r["_id"]: r["count"] for r in db.clauses.aggregate(pipeline)}

    return {
        "total_documents": total_documents,
        "total_clauses": total_clauses,
        "total_contradictions": total_contradictions,
        "risky_clauses": risky_clauses,
        "risk_distribution": risk_dist,
    }
