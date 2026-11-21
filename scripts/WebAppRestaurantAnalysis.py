from flask import Flask, render_template, request
import sqlite3
import pandas as pd
import plotly.express as px
import plotly
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
app = Flask(__name__, template_folder=str(ROOT / "templates"))
DB_FILE = ROOT / "restaurant_sentiment.db"

def query_data(restaurant=None, aspect=None, sentiment=None, location=None):
    conn = sqlite3.connect(DB_FILE)
    query = "SELECT * FROM sentiment_analysis WHERE 1=1"
    params = []

    if restaurant:
        query += " AND restaurant LIKE ?"
        params.append(f"%{restaurant}%")

    if aspect:
        query += " AND aspect LIKE ?"
        params.append(f"%{aspect}%")

    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")

    if sentiment:
        query += " AND sentiment = ?"
        params.append(sentiment)

    query += " ORDER BY sentiment_score DESC"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def generate_sentiment_by_aspect_plot(df):
    if df.empty:
        return None
    grouped = df.groupby('aspect', as_index=False)['sentiment_score'].mean()
    fig = px.bar(grouped, x='aspect', y='sentiment_score',
                 labels={'sentiment_score': 'Avg Sentiment Score'},
                 title='Average Sentiment Score by Aspect',
                 color='sentiment_score', height=400)
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    graphJSON = None

    if request.method == "POST":
        restaurant = request.form.get("restaurant")
        aspect = request.form.get("aspect")
        sentiment = request.form.get("sentiment")
        location = request.form.get("location")

        df = query_data(restaurant, aspect, sentiment, location)
        results = df.to_dict(orient="records")

        if not df.empty:
            if location:
                graphJSON = generate_sentiment_by_aspect_plot(df)

    return render_template("WebAppRestaurantAnalysis.html", results=results, graphJSON=graphJSON)

if __name__ == "__main__":
    app.run(port=5000)
