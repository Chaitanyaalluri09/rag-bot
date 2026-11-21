from app.embedder import embed_texts
from app.database import get_connection, search
from app.llm import build_prompt, generate_answer


def answer_question(question, k=5, session_id=None):
    query_vector = embed_texts([question])[0]

    with get_connection() as conn:
        results = search(conn, query_vector, k=k, session_id=session_id)

    if not results:
        return {"answer": "No documents are available to search yet.", "sources": []}

    prompt = build_prompt(question, results)
    answer = generate_answer(prompt)
    return {"answer": answer, "sources": results}