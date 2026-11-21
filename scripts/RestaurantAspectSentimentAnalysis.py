"""Extract whitelisted aspects and assign sentence-level VADER scores."""

import argparse
from pathlib import Path

import pandas as pd
import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from sentiment_utils import classify_sentiment

ROOT = Path(__file__).resolve().parents[1]
ASPECT_WHITELIST = {
    "food", "service", "ambience", "price", "staff", "cleanliness",
    "biryani", "pizza", "burger", "coffee", "taste", "waiter", "portion",
    "menu", "hygiene", "delivery", "music",
}


def extract_aspects(sentence):
    return {
        chunk.root.lemma_.lower()
        for chunk in sentence.noun_chunks
        if chunk.root.pos_ in {"NOUN", "PROPN"}
        and not chunk.root.is_stop
        and chunk.root.is_alpha
        and chunk.root.lemma_.lower() in ASPECT_WHITELIST
    }


def analyze_reviews(df, nlp, analyzer):
    records = []
    for _, row in df.iterrows():
        review = row.get("clean_reviews")
        if not isinstance(review, str) or not review.strip():
            continue
        for sentence in nlp(review).sents:
            aspects = extract_aspects(sentence)
            if not aspects:
                continue
            score = analyzer.polarity_scores(sentence.text)["compound"]
            for aspect in sorted(aspects):
                records.append({
                    "restaurant": row["name"],
                    "location": row["location"],
                    "aspect": aspect,
                    "sentiment_score": score,
                })

    columns = ["restaurant", "location", "aspect", "sentiment_score", "sentiment"]
    if not records:
        return pd.DataFrame(columns=columns)
    result = (
        pd.DataFrame(records)
        .groupby(["restaurant", "location", "aspect"], as_index=False)["sentiment_score"]
        .mean()
    )
    # Classify the displayed mean, so labels and scores remain consistent.
    result["sentiment"] = result["sentiment_score"].map(classify_sentiment)
    return result[columns]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "Datasets/demo_reviews.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "Datasets/restaurant_aspect_sentiments.csv")
    args = parser.parse_args()
    nlp = spacy.load("en_core_web_sm")
    result = analyze_reviews(pd.read_csv(args.input), nlp, SentimentIntensityAnalyzer())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"Saved {len(result)} aspect results to {args.output}")


if __name__ == "__main__":
    main()
