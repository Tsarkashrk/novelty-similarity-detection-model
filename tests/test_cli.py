"""End-to-end smoke test for the public command-line interface."""

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from thesis_novelty.cli import main


SAMPLE_TOPICS = Path(__file__).resolve().parents[1] / "data" / "sample_topics.csv"


class ThesisNoveltyCliTest(unittest.TestCase):
    def test_cli_returns_explainable_duplicate_assessment(self) -> None:
        args = [
            "thesis-novelty",
            "--data",
            str(SAMPLE_TOPICS),
            "--title",
            "Graph embeddings for recommendation of academic supervisors",
            "--abstract",
            "The model recommends supervisors using research profiles, graph embeddings and historical thesis topics.",
            "--keywords",
            "graph embeddings;supervisor recommendation;academic analytics",
            "--domain",
            "academic analytics",
            "--top-k",
            "3",
        ]
        output = io.StringIO()
        with patch("sys.argv", args), redirect_stdout(output):
            main()

        result = json.loads(output.getvalue())
        self.assertEqual(result["label"], "duplicate")
        self.assertEqual(result["similar_topics"][0]["topic_id"], "T004")
        self.assertLessEqual(len(result["similar_topics"]), 3)
        self.assertIn("semantic_similarity", result["components"])
        self.assertIn("keyword_uniqueness", result["components"])


if __name__ == "__main__":
    unittest.main()
