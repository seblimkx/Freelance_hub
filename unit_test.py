import unittest
from search_algo import SearchQuery
from sentence_transformers import SentenceTransformer
import search_algo  


# Set the same model used in SearchQuery
search_algo.model = SentenceTransformer("all-MiniLM-L6-v2")


class TestSearchQuery(unittest.TestCase):
    def setUp(self):
        self.items = [
            type("MockItem", (), {"title": "Apple", "description": "A red fruit"}),
            type("MockItem", (), {"title": "Banana", "description": "A yellow fruit"}),
            type("MockItem", (), {"title": "Car", "description": "A fast vehicle"}),
        ]
        self.search_engine = SearchQuery(self.items)

    def test_search_returns_list(self):
        results = self.search_engine.search("fruit")
        self.assertIsInstance(results, list)
        self.assertTrue(all(isinstance(r, tuple) for r in results))
        self.assertTrue(all(len(r) == 2 for r in results))

    def test_search_ranking_order(self):
        results = self.search_engine.search("fruit")
        scores = [score for _, score in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_no_crash_with_empty_query(self):
        results = self.search_engine.search("")
        self.assertIsInstance(results, list)


if __name__ == "__main__":
    unittest.main()
