from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_MODEL

_model = None


def get_model():
    """Load the model once and reuse it."""
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def embed_texts(texts, show_progress=False):
    """Turn a list of texts into a list of vectors."""
    return get_model().encode(texts, show_progress_bar=show_progress)