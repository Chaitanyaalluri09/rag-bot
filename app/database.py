import psycopg
from pgvector.psycopg import register_vector
from app.config import DATABASE_URL


def get_connection():
    conn = psycopg.connect(DATABASE_URL, autocommit=True)
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)
    return conn


def init_db(conn):
    """Create tables and the vector index if they don't exist yet."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id          SERIAL PRIMARY KEY,
            filename    TEXT NOT NULL,
            uploaded_at TIMESTAMPTZ DEFAULT now()
        )
        """
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


def add_document(conn, filename, chunks, vectors):
    """Save a document and all its chunks in one transaction."""
    with conn.transaction():
        # Re-ingesting the same file replaces the old copy
        conn.execute("DELETE FROM documents WHERE filename = %s", (filename,))
        doc_id = conn.execute(
            "INSERT INTO documents (filename) VALUES (%s) RETURNING id", (filename,)
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


def search(conn, query_vector, k=5):
    """Return the k chunks closest in meaning to the query vector."""
    rows = conn.execute(
        """
        SELECT d.filename, c.page, c.content, c.embedding <=> %s AS distance
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        ORDER BY c.embedding <=> %s
        LIMIT %s
        """,
        (query_vector, query_vector, k),
    ).fetchall()
    return [
        {"filename": f, "page": p, "content": text, "distance": float(dist)}
        for f, p, text, dist in rows
    ]