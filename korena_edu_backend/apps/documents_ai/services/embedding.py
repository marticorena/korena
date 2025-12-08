from typing import List

from fastembed import TextEmbedding

_model: TextEmbedding | None = None


def _get_model() -> TextEmbedding:
    """Return a singleton TextEmbedding model instance.

    Uses a lightweight open-source model that runs locally on CPU.
    """
    global _model

    if _model is None:
        _model = TextEmbedding(
            model_name="BAAI/bge-small-en-v1.5",
        )

    return _model


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Return embedding vectors for a list of texts.

    Args:
        texts: List of input texts to embed.

    Returns:
        List[List[float]]: List of embedding vectors, one per input text.
    """
    if not texts:
        return []

    model = _get_model()
    embeddings_iter = model.embed(texts)
    embeddings: List[List[float]] = [list(vec) for vec in embeddings_iter]

    return embeddings


def get_embedding(text: str) -> List[float]:
    """Return an embedding vector for a single text.

    This is a convenience wrapper over get_embeddings.
    """
    embeddings = get_embeddings([text])

    if not embeddings:

        return []

    return embeddings[0]
