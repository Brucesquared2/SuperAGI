import unittest
from unittest.mock import patch
from superagi.vector_embeddings.vector_embedding_factory import VectorEmbeddingFactory
from superagi.vector_embeddings.antigravity import Antigravity


class TestAntigravityEmbedding(unittest.TestCase):

    def test_get_vector_embeddings_from_chunks(self):
        uuid = [1, 2]
        embeds = [[1, 2, 3], [4, 5, 6]]
        metadata = [
            {"text": "test", "chunk": "chunk", "knowledge_name": "knowledge"},
            {"text": "test2", "chunk": "chunk2", "knowledge_name": "knowledge2"},
        ]
        antigravity = Antigravity(uuid, embeds, metadata)
        result = antigravity.get_vector_embeddings_from_chunks()
        self.assertEqual(result['ids'], uuid)
        self.assertEqual(result['embeddings'], embeds)
        self.assertEqual(result['metadata'], metadata)

    @patch("superagi.vector_embeddings.antigravity.Antigravity.__init__", return_value=None)
    def test_build_vector_storage_antigravity(self, mock_init):
        test_data = {
            "1": {"id": 1, "embeds": [1, 2, 3], "text": "test", "chunk": "chunk", "knowledge_name": "knowledge"},
            "2": {"id": 2, "embeds": [4, 5, 6], "text": "test2", "chunk": "chunk2", "knowledge_name": "knowledge2"},
        }

        vector_storage = VectorEmbeddingFactory.build_vector_storage('Antigravity', test_data)

        mock_init.assert_called_once_with(
            [1, 2],
            [[1, 2, 3], [4, 5, 6]],
            [
                {"text": "test", "chunk": "chunk", "knowledge_name": "knowledge"},
                {"text": "test2", "chunk": "chunk2", "knowledge_name": "knowledge2"},
            ],
        )
        self.assertIsInstance(vector_storage, Antigravity)


if __name__ == "__main__":
    unittest.main()
