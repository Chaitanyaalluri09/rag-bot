from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY, GEMINI_MODEL

_client = None


def get_client():
    global _client
    if _client is None:
        if not GEMINI_API_KEY or not GEMINI_MODEL:
            raise RuntimeError("Set GEMINI_API_KEY and GEMINI_MODEL in your .env file.")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def build_prompt(question, results):
    """Put the retrieved chunks and the question into one prompt."""
    blocks = []
    for i, r in enumerate(results, start=1):
        blocks.append(f"[{i}] (source: {r['filename']}, page {r['page']})\n{r['content']}")
    context = "\n\n".join(blocks)

    return f"""You are a careful assistant that answers questions using only the context below.

Rules:
- Use ONLY the information in the context. Do not use outside knowledge.
- If the context does not contain the answer, reply exactly: "I couldn't find that in the document."
- After each fact, cite the source number like [1] or [2].
- Be clear and concise.

Context:
{context}

Question: {question}

Answer:"""


def generate_answer(prompt):
    response = get_client().models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.2),
    )
    return response.text