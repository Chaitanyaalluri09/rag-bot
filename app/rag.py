from app.embedder import embed_texts
from app.database import get_connection, search
from app.llm import build_prompt, generate_answer


def answer_question(question, k=5):
    query_vector = embed_texts([question])[0]

    with get_connection() as conn:  # closes automatically when done
        results = search(conn, query_vector, k=k)

    if not results:
        return {"answer": "No documents have been ingested yet.", "sources": []}

    prompt = build_prompt(question, results)
    answer = generate_answer(prompt)
    return {"answer": answer, "sources": results}