from __future__ import annotations

import logging
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


logger = logging.getLogger(__name__)

# Default model uses sentence-transformers local cache (e.g. HF_HOME / cache_dir).
# No extra config needed to avoid repeated downloads per request.
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"

_singleton_client: EmbeddingClient | None = None


class EmbeddingClient:
    """
    Thin wrapper around a local sentence-transformers model.
    Uses a small, stable model: all-MiniLM-L6-v2 (384 dims).
    Intended to be used as a singleton via get_embedding_client() so the model
    is loaded once per process and reused for all requests.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
        self.model_name = model_name
        logger.info(
            "Loading embedding model '%s' (first time in this process; will reuse for subsequent requests).",
            model_name,
        )
        self._model = SentenceTransformer(model_name)
        self.embedding_dimension: int = int(
            getattr(self._model, "get_sentence_embedding_dimension", lambda: 384)()
        )
        logger.info(
            "Embedding model '%s' loaded with dimension %d. Singleton ready.",
            model_name,
            self.embedding_dimension,
        )

    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 128,
        normalize: bool = True,
    ) -> List[List[float]]:
        """
        Embed a list of texts into dense vectors.
        Returns a list of embedding_dimension-dimensional float vectors.
        """
        if not texts:
            return []

        logger.debug(
            "Embedding %d texts with batch_size=%d (using cached model).",
            len(texts),
            batch_size,
        )
        embeddings: np.ndarray = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=normalize,
        )
        logger.debug("Embedding completed. Shape=%s.", embeddings.shape)
        return embeddings.astype(float).tolist()


def get_embedding_client(model_name: str = DEFAULT_MODEL_NAME) -> EmbeddingClient:
    """
    Return a singleton EmbeddingClient instance. The model is loaded once per
    process and reused for all requests to avoid high latency on every semantic
    search.
    """
    global _singleton_client
    if _singleton_client is None:
        _singleton_client = EmbeddingClient(model_name=model_name)
    else:
        logger.debug("Reusing cached embedding model (singleton).")
    return _singleton_client

