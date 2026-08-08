import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from foundry_ai_basics.ai.search import search_documents


class FakeSearchClient:
    def __init__(self, results):
        self.results = results
        self.search_kwargs = None

    def search(self, **kwargs):
        self.search_kwargs = kwargs
        return self.results


class SearchTests(unittest.TestCase):
    def test_search_documents_uses_vector_query_and_returns_matches(self):
        search_client = FakeSearchClient(
            [
                {
                    "id": "order-1",
                    "title": "Order: 55-inch 4K Smart TV",
                    "content": "Customer purchased a Contoso smart TV.",
                    "category": "order",
                    "@search.score": 1.5,
                    "@search.reranker_score": 2.25,
                }
            ]
        )

        with patch(
            "foundry_ai_basics.ai.search.generate_embeddings",
            return_value=[0.1, 0.2, 0.3],
        ):
            with redirect_stdout(io.StringIO()):
                matches = search_documents(
                    search_client,
                    openai_client=object(),
                    embedding_deployment_name="text-embedding-3-small",
                    question="Which TV was ordered?",
                    top=3,
                )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["id"], "order-1")
        self.assertEqual(
            search_client.search_kwargs["search_text"],
            "Which TV was ordered?",
        )
        self.assertEqual(search_client.search_kwargs["query_type"], "semantic")
        self.assertEqual(search_client.search_kwargs["top"], 3)

        vector_query = search_client.search_kwargs["vector_queries"][0]
        self.assertEqual(vector_query.vector, [0.1, 0.2, 0.3])
        self.assertEqual(vector_query.fields, "content_vector")
        self.assertEqual(vector_query.k_nearest_neighbors, 3)

    def test_search_documents_returns_empty_list_when_no_matches(self):
        search_client = FakeSearchClient([])

        with patch(
            "foundry_ai_basics.ai.search.generate_embeddings",
            return_value=[0.1, 0.2, 0.3],
        ):
            with redirect_stdout(io.StringIO()):
                matches = search_documents(
                    search_client,
                    openai_client=object(),
                    embedding_deployment_name="text-embedding-3-small",
                    question="missing",
                )

        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
