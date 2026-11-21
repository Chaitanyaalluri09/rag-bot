import os
import sys

from app.pdf_reader import read_pdf
from app.chunker import chunk_pages
from app.embedder import embed_texts
from app.database import get_connection, init_db, add_document


def main():
    if len(sys.argv) != 2:
        print("Usage: python ingest.py data/mydoc.pdf")
        sys.exit(1)

    path = sys.argv[1]
    pages = read_pdf(path)
    chunks = chunk_pages(pages)
    print(f"{len(pages)} pages -> {len(chunks)} chunks. Creating embeddings...")

    vectors = embed_texts([c["content"] for c in chunks], show_progress=True)

    conn = get_connection()
    init_db(conn)
    doc_id = add_document(conn, os.path.basename(path), chunks, vectors)
    print(f"Saved '{path}' as document {doc_id}.")


if __name__ == "__main__":
    main()