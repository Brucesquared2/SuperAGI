import unittest
from unittest.mock import MagicMock
from superagi.vector_store.antigravity import Antigravity
from superagi.vector_store.document import Document


class TestAntigravityVectorStore(unittest.TestCase):

    def _make_store(self):
        mock_model = MagicMock()
        mock_model.get_embedding.side_effect = lambda text: [1.0, 0.0] if text == "hello" else [0.0, 1.0]
        return Antigravity("test_collection", mock_model)

    def test_add_embeddings_to_vector_db(self):
        store = Antigravity("col")
        store.add_embeddings_to_vector_db({
            'ids': ['a', 'b'],
            'embeddings': [[1, 2], [3, 4]],
            'metadata': [{'text': 'foo'}, {'text': 'bar'}],
        })
        self.assertEqual(len(store._store), 2)
        self.assertEqual(store._store['a']['metadata']['text'], 'foo')
        self.assertEqual(store._store['b']['embedding'], [3, 4])

    def test_add_texts(self):
        store = self._make_store()
        ids = store.add_texts(["hello", "world"], ids=["id1", "id2"])
        self.assertEqual(ids, ["id1", "id2"])
        self.assertIn("id1", store._store)
        self.assertEqual(store._store["id1"]['metadata']['text'], "hello")

    def test_get_matching_text_returns_documents(self):
        store = self._make_store()
        store.add_texts(["hello"], ids=["id1"])
        result = store.get_matching_text("hello", top_k=1)
        self.assertIn('documents', result)
        self.assertIn('search_res', result)
        self.assertEqual(len(result['documents']), 1)
        self.assertIsInstance(result['documents'][0], Document)

    def test_delete_embeddings_from_vector_db(self):
        store = Antigravity("col")
        store.add_embeddings_to_vector_db({
            'ids': ['x'],
            'embeddings': [[1, 0]],
            'metadata': [{'text': 'to delete'}],
        })
        store.delete_embeddings_from_vector_db(['x'])
        self.assertNotIn('x', store._store)

    def test_get_index_stats(self):
        store = Antigravity("col")
        store.add_embeddings_to_vector_db({
            'ids': ['a'],
            'embeddings': [[1]],
            'metadata': [{}],
        })
        stats = store.get_index_stats()
        self.assertEqual(stats['vector_count'], 1)

    def test_cosine_similarity(self):
        self.assertAlmostEqual(Antigravity._cosine_similarity([1, 0], [1, 0]), 1.0)
        self.assertAlmostEqual(Antigravity._cosine_similarity([1, 0], [0, 1]), 0.0)
        self.assertEqual(Antigravity._cosine_similarity([], []), 0.0)
        self.assertEqual(Antigravity._cosine_similarity([0, 0], [1, 1]), 0.0)


if __name__ == "__main__":
    unittest.main()
