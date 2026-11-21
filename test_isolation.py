from app.database import get_connection, list_documents, search
from app.embedder import embed_texts
from app.ingest_service import ingest_pdf

# Alice uploads a private copy under a different name
ingest_pdf("data/mydoc.pdf", session_id="test-alice", display_name="alice-private.pdf")

vec = embed_texts(["any question"])[0]

with get_connection() as conn:
    for who in ["test-alice", "test-bob", None]:
        docs = [d["filename"] for d in list_documents(conn, who)]
        hits = {r["filename"] for r in search(conn, vec, k=50, session_id=who)}
        print(f"{who!s:12} sees docs: {docs}")
        print(f"{'':12} search hits come from: {sorted(hits)}\n")

    conn.execute("DELETE FROM documents WHERE session_id LIKE 'test-%'")
    print("Cleaned up test data.")