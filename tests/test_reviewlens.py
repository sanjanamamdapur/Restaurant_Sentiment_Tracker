"""Regression tests for sentiment scoring and the runnable project workflow."""

import importlib.util
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

import pandas as pd
import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sentiment_utils import classify_sentiment
from RestaurantAspectSentimentAnalysis import analyze_reviews


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SentimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nlp = spacy.load("en_core_web_sm")
        cls.analyzer = SentimentIntensityAnalyzer()

    def test_threshold_boundaries_and_original_regression(self):
        for score, expected in [
            (-1, "negative"), (-0.05, "negative"), (-0.049, "neutral"),
            (0, "neutral"), (0.049, "neutral"), (0.05, "positive"),
            (0.6, "positive"), (1, "positive"),
        ]:
            with self.subTest(score=score):
                self.assertEqual(classify_sentiment(score), expected)

    def test_distinct_sentences_keep_opposite_aspect_sentiments(self):
        reviews = pd.DataFrame([{
            "name": "Cafe", "location": "Town",
            "clean_reviews": "The food was excellent! The service was terrible.",
        }])
        result = analyze_reviews(reviews, self.nlp, self.analyzer).set_index("aspect")
        self.assertEqual(result.loc["food", "sentiment"], "positive")
        self.assertEqual(result.loc["service", "sentiment"], "negative")

    def test_mean_score_determines_aggregate_label(self):
        reviews = pd.DataFrame([
            {"name": "Cafe", "location": "Town", "clean_reviews": text}
            for text in ["The food was excellent!", "The food was terrible."]
        ])
        result = analyze_reviews(reviews, self.nlp, self.analyzer)
        expected = sum(self.analyzer.polarity_scores(text)["compound"]
                       for text in reviews["clean_reviews"]) / 2
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result.iloc[0]["sentiment_score"], expected)
        self.assertEqual(result.iloc[0]["sentiment"], classify_sentiment(expected))

    def test_no_aspects_and_missing_reviews_produce_empty_table(self):
        reviews = pd.DataFrame([
            {"name": "Cafe", "location": "Town", "clean_reviews": text}
            for text in ["It is here.", None, ""]
        ])
        result = analyze_reviews(reviews, self.nlp, self.analyzer)
        self.assertTrue(result.empty)
        self.assertIn("sentiment", result.columns)


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.project = Path(cls.temp.name) / "project"
        for folder in ["scripts", "templates", "schemas"]:
            shutil.copytree(ROOT / folder, cls.project / folder,
                            ignore=shutil.ignore_patterns("__pycache__", "*.xlsx"))
        (cls.project / "Datasets").mkdir()
        reviews = pd.read_csv(ROOT / "Datasets/demo_reviews.csv")
        reviews.loc[len(reviews)] = ["Chef's Cafe", "Demo District", "The food was excellent!"]
        reviews.to_csv(cls.project / "Datasets/demo_reviews.csv", index=False)
        cls.run_script("RestaurantAspectSentimentAnalysis.py")
        cls.run_script("StoreInDatabase.py")
        cls.run_script("StoreInDatabase.py")
        cls.run_script("XMLGeneration.py")
        cls.web = load_module("web_test", cls.project / "scripts/WebAppRestaurantAnalysis.py")
        cls.api = load_module("api_test", cls.project / "scripts/RestaurantAspectSentimentAPI.py")
        cls.web.app.testing = True
        cls.api.app.testing = True

    @classmethod
    def run_script(cls, filename):
        # Deliberately run outside the project to check file-path handling.
        completed = subprocess.run(
            [sys.executable, str(cls.project / "scripts" / filename)],
            cwd=cls.temp.name, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        if completed.returncode:
            raise AssertionError(completed.stdout + completed.stderr)

    def test_database_rebuild_does_not_duplicate_rows(self):
        expected = len(pd.read_csv(self.project / "Datasets/restaurant_aspect_sentiments.csv"))
        with sqlite3.connect(self.project / "restaurant_sentiment.db") as conn:
            actual = conn.execute("SELECT COUNT(*) FROM sentiment_analysis").fetchone()[0]
        self.assertGreater(actual, 0)
        self.assertEqual(actual, expected)

    def test_original_data_cleaning_preserves_nlp_cues(self):
        raw_review = "RATED\nThe food wasn't good! The service was GREAT."
        raw = pd.DataFrame([{
            "name": "Fixture Cafe", "location": "Town", "rate": "4.0/5",
            "cuisines": "Cafe", "approx_cost(for two people)": "1,000",
            "reviews_list": repr([("Rated 4.0", raw_review)]),
        }] * 10)
        raw.to_csv(self.project / "Datasets/zomato.csv", index=False)
        self.run_script("DataCleaning.py")
        result = pd.read_csv(self.project / "Datasets/cleaned_restaurant_reviews.csv")
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["clean_reviews"],
                         "The food wasn't good! The service was GREAT.")
        self.assertEqual(result.iloc[0]["rate"], 4.0)
        self.assertEqual(result.iloc[0]["approx_costfor_two_people"], 1000.0)

    def test_web_home_and_filtered_chart(self):
        with self.web.app.test_client() as client:
            self.assertEqual(client.get("/").status_code, 200)
            response = client.post("/", data={"location": "Demo District", "sentiment": "negative"})
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Demo Cafe", response.data)
            self.assertIn(b"Plotly.newPlot", response.data)
            self.assertNotIn(b"Demo Bistro", response.data)
            empty = client.post("/", data={"location": "Missing Place"})
            self.assertIn(b"No results found", empty.data)

    def test_all_api_shapes_validate_and_quote_names_work(self):
        with self.api.app.test_client() as client:
            for path, schema in [
                ("/api/sentiments", "full"),
                ("/api/sentiments/Demo%20Cafe", "restaurant"),
                ("/api/sentiments/Demo%20Cafe/food", "aspect"),
                ("/api/sentiments/Chef%27s%20Cafe/food", "aspect"),
            ]:
                with self.subTest(path=path):
                    response = client.get(path)
                    self.assertEqual(response.status_code, 200)
                    self.api.validate_with_relaxng(response.get_data(as_text=True), self.api.SCHEMAS[schema])

    def test_unknown_api_names_return_404(self):
        with self.api.app.test_client() as client:
            self.assertEqual(client.get("/api/sentiments/Unknown").status_code, 404)
            self.assertEqual(client.get("/api/sentiments/Demo%20Cafe/unknown").status_code, 404)


if __name__ == "__main__":
    unittest.main()
