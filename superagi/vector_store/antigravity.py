from typing import Any, Dict, Iterable, List, Optional

from superagi.vector_store.base import VectorStore
from superagi.vector_store.document import Document


class Antigravity(VectorStore):
    """
    Antigravity in-memory vector store.

    Attributes:
        collection_name : The name of the collection.
        embedding_model : The embedding model used for text queries.
        text_field : The field name for the text content in metadata.
    """

    def __init__(
            self,
            collection_name: str,
            embedding_model: Optional[Any] = None,
            text_field: str = 'text',
    ):
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.text_field = text_field
        self._store: Dict[str, Dict] = {}

    def add_texts(
            self,
            texts: Iterable[str],
            metadatas: Optional[List[dict]] = None,
            ids: Optional[List[str]] = None,
            **kwargs: Any,
    ) -> List[str]:
        """Add texts to the in-memory store."""
        import uuid as _uuid
        texts = list(texts)
        ids = ids or [str(_uuid.uuid4()) for _ in texts]
        metadatas = metadatas or [{} for _ in texts]
        for text, meta, doc_id in zip(texts, metadatas, ids):
            embedding = self.embedding_model.get_embedding(text) if self.embedding_model else []
            entry = dict(meta)
            entry[self.text_field] = text
            self._store[doc_id] = {'embedding': embedding, 'metadata': entry}
        return ids

    def get_matching_text(self, query: str, top_k: int = 5, metadata: Optional[dict] = None,
                          **kwargs: Any) -> Dict:
        """Return docs most similar to query by cosine similarity."""
        if not self._store:
            return {'documents': [], 'search_res': f'Query: {query}\n'}

        query_embedding = self.embedding_model.get_embedding(query) if self.embedding_model else []
        scored = []
        for doc_id, entry in self._store.items():
            score = self._cosine_similarity(query_embedding, entry['embedding'])
            if metadata:
                if not all(entry['metadata'].get(k) == v for k, v in metadata.items()):
                    continue
            scored.append((score, doc_id, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]

        documents = [
            Document(text_content=e['metadata'].get(self.text_field, ''), metadata=e['metadata'])
            for _, _, e in top
        ]
        search_res = f'Query: {query}\n'
        for i, (_, _, entry) in enumerate(top):
            search_res += f"Chunk{i}: \n{entry['metadata'].get(self.text_field, '')}\n"
        return {'documents': documents, 'search_res': search_res}

    def get_index_stats(self) -> dict:
        """Returns stats about the in-memory store."""
        return {'vector_count': len(self._store)}

    def add_embeddings_to_vector_db(self, embeddings: dict) -> None:
        """Load pre-computed embeddings into the in-memory store."""
        ids = embeddings.get('ids', [])
        vecs = embeddings.get('embeddings', [])
        metas = embeddings.get('metadata', [])
        for doc_id, embedding, meta in zip(ids, vecs, metas):
            entry = dict(meta) if meta else {}
            self._store[doc_id] = {'embedding': embedding, 'metadata': entry}

    def delete_embeddings_from_vector_db(self, ids: List[str]) -> None:
        """Delete embeddings from the in-memory store."""
        for doc_id in ids:
            self._store.pop(doc_id, None)

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
