import sys

from app.embedder import embed_texts
from app.database import get_connection, search


def main():
    if len(sys.argv) < 2:
        print('Usage: python search_docs.py "your question"')
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    query_vector = embed_texts([question])[0]

    conn = get_connection()
    results = search(conn, query_vector, k=5)

    for r in results:
        print(f"[{r['distance']:.3f}] {r['filename']} - page {r['page']}")
        print(r["content"][:400])
        print("-" * 60)


if __name__ == "__main__":
    main()