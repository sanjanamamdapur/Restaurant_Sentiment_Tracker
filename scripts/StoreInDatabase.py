import sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Load your final CSV
csv_file = ROOT / "Datasets/restaurant_aspect_sentiments.csv"
df = pd.read_csv(csv_file)

# Connect to (or create) a SQLite database file
conn = sqlite3.connect(ROOT / "restaurant_sentiment.db")
cursor = conn.cursor()

# Create a table
cursor.execute("""
CREATE TABLE IF NOT EXISTS sentiment_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant TEXT,
    location TEXT,
    aspect TEXT,
    sentiment_score REAL,
    sentiment TEXT
)
""")
conn.commit()

# Insert data from DataFrame into the database
cursor.execute("DELETE FROM sentiment_analysis")
df.to_sql("sentiment_analysis", conn, if_exists='append', index=False)

# Example: Top 5 most positively reviewed aspects
query = """
SELECT restaurant, aspect, AVG(sentiment_score) as avg_score
FROM sentiment_analysis
WHERE sentiment = 'positive'
GROUP BY restaurant, aspect
ORDER BY avg_score DESC
LIMIT 5
"""
top_positive = pd.read_sql_query(query, conn)
print(top_positive)

conn.close()
