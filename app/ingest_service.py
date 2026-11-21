import os

from app.chunker import chunk_pages
from app.config import (
    MAX_DOCS_PER_SESSION,
    MAX_PAGES,
    MAX_PDF_MB,
    MAX_TOTAL_CHUNKS,
)
from app.database import (
    add_document,
    count_session_documents,
    delete_expired_sessions,
    get_connection,
    init_db,
    total_chunks,
)
from app.embedder import embed_texts
from app.pdf_reader import read_pdf


class IngestError(ValueError):
    """A problem with the file or the demo limits. Safe to show to the user."""


def ingest_pdf(path, session_id=None, display_name=None, show_progress=False):
    """Read, chunk, embed and store one PDF.

    session_id=None means your own trusted ingestion (shared, no limits).
    A session_id means a visitor upload, so all demo limits apply.
    """
    is_visitor = session_id is not None
    filename = display_name or os.path.basename(path)

    if is_visitor and os.path.getsize(path) > MAX_PDF_MB * 1024 * 1024:
        raise IngestError(f"This file is too large. The demo limit is {MAX_PDF_MB} MB.")

    try:
        pages = read_pdf(path)
    except Exception as e:
        raise IngestError("This file could not be read as a PDF.") from e

    if is_visitor and len(pages) > MAX_PAGES:
        raise IngestError(
            f"This PDF has {len(pages)} pages. The demo limit is {MAX_PAGES}."
        )

    chunks = chunk_pages(pages)
    if not chunks:
        raise IngestError("No readable text found in this PDF (it may be scanned).")

    # Cheap checks first, before the slow embedding step
    with get_connection() as conn:
        init_db(conn)
        if is_visitor:
            delete_expired_sessions(conn)
            if count_session_documents(conn, session_id) >= MAX_DOCS_PER_SESSION:
                raise IngestError(
                    f"You can upload up to {MAX_DOCS_PER_SESSION} documents per session."
                )
            if total_chunks(conn) + len(chunks) > MAX_TOTAL_CHUNKS:
                raise IngestError(
                    "The demo's storage is full right now. Please try again later."
                )

    vectors = embed_texts([c["content"] for c in chunks], show_progress=show_progress)

    with get_connection() as conn:
        doc_id = add_document(conn, filename, chunks, vectors, session_id)

    return {
        "document_id": doc_id,
        "filename": filename,
        "pages": len(pages),
        "chunks": len(chunks),
    }