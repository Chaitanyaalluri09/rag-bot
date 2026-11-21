import psycopg
from pgvector.psycopg import register_vector

from app.config import DATABASE_URL, SESSION_TTL_HOURS


def get_connection():
    conn = psycopg.connect(DATABASE_URL, autocommit=True)
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)
    return conn


def init_db(conn):
    """Create tables and indexes if they don't exist yet."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id          SERIAL PRIMARY KEY,
            filename    TEXT NOT NULL,
            uploaded_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    # NEW: which visitor owns the document (NULL = shared sample document)
    conn.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS session_id TEXT")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS documents_session_idx ON documents (session_id)"
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chunks (
            id          SERIAL PRIMARY KEY,
            document_id INT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            page        INT,
            chunk_index INT,
            content     TEXT NOT NULL,
            embedding   vector(384)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS chunks_embedding_idx
        ON chunks USING hnsw (embedding vector_cosine_ops)
        """
    )


def add_document(conn, filename, chunks, vectors, session_id=None):
    """Save a document and its chunks in one transaction."""
    with conn.transaction():
        # Re-uploading the same file name replaces the old copy (same owner only)
        conn.execute(
            """
            DELETE FROM documents
            WHERE filename = %s AND session_id IS NOT DISTINCT FROM %s::text
            """,
            (filename, session_id),
        )
        doc_id = conn.execute(
            "INSERT INTO documents (filename, session_id) VALUES (%s, %s) RETURNING id",
            (filename, session_id),
        ).fetchone()[0]
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO chunks (document_id, page, chunk_index, content, embedding)
                VALUES (%s, %s, %s, %s, %s)
                """,
                [
                    (doc_id, c["page"], c["chunk_index"], c["content"], vec)
                    for c, vec in zip(chunks, vectors)
                ],
            )
    return doc_id


def search(conn, query_vector, k=5, session_id=None):
    """Closest chunks among shared documents plus this visitor's own."""
    rows = conn.execute(
        """
        SELECT d.filename, c.page, c.content, c.embedding <=> %s AS distance
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE d.session_id IS NULL OR d.session_id = %s::text
        ORDER BY c.embedding <=> %s
        LIMIT %s
        """,
        (query_vector, session_id, query_vector, k),
    ).fetchall()
    return [
        {"filename": f, "page": p, "content": text, "distance": float(dist)}
        for f, p, text, dist in rows
    ]


def list_documents(conn, session_id=None):
    """Documents this visitor can see, with chunk counts."""
    rows = conn.execute(
        """
        SELECT d.id, d.filename, d.uploaded_at, count(c.id), d.session_id IS NULL
        FROM documents d
        LEFT JOIN chunks c ON c.document_id = d.id
        WHERE d.session_id IS NULL OR d.session_id = %s::text
        GROUP BY d.id
        ORDER BY d.id
        """,
        (session_id,),
    ).fetchall()
    return [
        {"id": i, "filename": f, "uploaded_at": t, "chunks": n, "shared": shared}
        for i, f, t, n, shared in rows
    ]


# ---------- NEW: limits and cleanup ----------

def delete_expired_sessions(conn):
    """Delete visitor uploads older than the time-to-live."""
    conn.execute(
        """
        DELETE FROM documents
        WHERE session_id IS NOT NULL
          AND uploaded_at < now() - make_interval(hours => %s)
        """,
        (SESSION_TTL_HOURS,),
    )


def count_session_documents(conn, session_id):
    return conn.execute(
        "SELECT count(*) FROM documents WHERE session_id = %s", (session_id,)
    ).fetchone()[0]


def total_chunks(conn):
    return conn.execute("SELECT count(*) FROM chunks").fetchone()[0]