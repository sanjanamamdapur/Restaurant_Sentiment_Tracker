import pandas as pd
import re
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Load CSV
df = pd.read_csv(ROOT / "Datasets/zomato.csv")

# Step 1: Drop columns not needed for sentiment
columns_to_keep = [
    "name", "location", "rate", "cuisines", "approx_cost(for two people)",
    "reviews_list"
]
df = df[columns_to_keep]

# Step 2: Rename columns for easier access
df.columns = [col.strip().lower().replace(" ", "_").replace("(", "").replace(")", "") for col in df.columns]

# Step 3: Clean `rate` column (remove "/5", handle 'NEW', 'NaN')
def clean_rate(rate):
    if isinstance(rate, str) and "/5" in rate:
        try:
            return float(rate.split("/")[0].strip())
        except:
            return None
    return None

df["rate"] = df["rate"].apply(clean_rate)

# Step 4: Clean cost column: remove commas, convert to float
df["approx_costfor_two_people"] = (
    df["approx_costfor_two_people"]
    .astype(str)
    .str.replace(",", "")
    .apply(lambda x: float(x) if x.replace('.', '', 1).isdigit() else None)
)

# Step 5: Clean and extract reviews
def extract_reviews(text):
    try:
        reviews = ast.literal_eval(text)  # turns string list into actual list
        # Preserve punctuation, negation, and case used by spaCy and VADER.
        return "\n\n".join([
            re.sub(r"^\s*RATED\s*", "", r[1]).strip()
            for r in reviews
            if isinstance(r, tuple) and len(r) > 1 and isinstance(r[1], str)
        ])
    except:
        return ""

df["clean_reviews"] = df["reviews_list"].apply(extract_reviews)

# Step 6: Drop rows with empty reviews
df = df[df["clean_reviews"].str.strip() != ""]

# Step 7: Optional - fill missing values in location or cuisines
df["location"] = df["location"].fillna("Unknown")
df["cuisines"] = df["cuisines"].fillna("Various")

# Step 8: Keep a sample if large
df = df.sample(frac=0.1, random_state=42)  # optional: use only 10% of data

# Step 9: Save cleaned data
df.to_csv(ROOT / "Datasets/cleaned_restaurant_reviews.csv", index=False)

print("Cleaned data saved to Datasets/cleaned_restaurant_reviews.csv")
