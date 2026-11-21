import os

from app.pdf_reader import read_pdf
from app.chunker import chunk_pages
from app.embedder import embed_texts
from app.database import get_connection, init_db, add_document


def ingest_pdf(path, show_progress=False):
    """Read, chunk, embed and store one PDF. Returns a short summary."""
    pages = read_pdf(path)
    chunks = chunk_pages(pages)
    if not chunks:
        raise ValueError("No readable text found in this PDF (it may be scanned).")

    vectors = embed_texts([c["content"] for c in chunks], show_progress=show_progress)

    filename = os.path.basename(path)
    with get_connection() as conn:
        init_db(conn)
        doc_id = add_document(conn, filename, chunks, vectors)

    return {
        "document_id": doc_id,
        "filename": filename,
        "pages": len(pages),
        "chunks": len(chunks),
    }