# ReviewLens: Restaurant Sentiment Tracker

ReviewLens is a Python web application that explores what restaurant reviews say about food, service, ambience, and other predefined aspects. It cleans review data, extracts aspects with spaCy, scores sentiment with VADER, and makes the results available through a Flask interface and an XML API.

## Academic context

This project was developed as a group assignment for an academic subject during MSc Computer Science studies. It demonstrates an end-to-end workflow involving NLP, structured data, XML schema validation, and web development. It is an educational prototype; no custom sentiment model was trained and no benchmark accuracy is claimed.

### Authors

- Sanjana Mamdapur
- Rohit Poojary
- Udit Pande

## Features

- Extracts aspect nouns from a fixed whitelist using spaCy noun chunks.
- Assigns VADER compound scores to sentences mentioning those aspects.
- Averages scores by restaurant, location, and aspect.
- Stores results in SQLite and exports XML validated with RelaxNG schemas.
- Filters results by aspect, location, and sentiment in a Flask web interface.
- Displays average aspect sentiment in a Plotly chart when a location filter is supplied.
- Exposes read-only XML endpoints for all results, a restaurant, or an aspect.

## Setup and demo

Use **Python 3.11** with the pinned dependencies in `requirements.txt`. Run the following commands from the project root. The included demo reviews are fictional, so the demo does not require downloading the original dataset.

### Windows (PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

.\.venv\Scripts\python.exe scripts/RestaurantAspectSentimentAnalysis.py
.\.venv\Scripts\python.exe scripts/StoreInDatabase.py
.\.venv\Scripts\python.exe scripts/XMLGeneration.py
.\.venv\Scripts\python.exe scripts/WebAppRestaurantAnalysis.py
```

### macOS / Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

python scripts/RestaurantAspectSentimentAnalysis.py
python scripts/StoreInDatabase.py
python scripts/XMLGeneration.py
python scripts/WebAppRestaurantAnalysis.py
```

Open **http://127.0.0.1:5000**. Try the location `Demo District` or `Sample Square`, then select Search. Blank filters return all records. The chart requires a location filter. Plotly.js is loaded from a CDN and needs an internet connection.

The analysis command defaults to `Datasets/demo_reviews.csv` and writes `Datasets/restaurant_aspect_sentiments.csv`. The next two commands rebuild the local database and XML from that CSV. **Rebuilding replaces existing analysis results**; running the database step again does not append duplicates. Previously generated results must be rebuilt to use the corrected sentiment thresholds.

### XML API

In another terminal, start the API using the virtual environment's Python:

```powershell
.\.venv\Scripts\python.exe scripts/RestaurantAspectSentimentAPI.py
```

On macOS/Linux, use `python scripts/RestaurantAspectSentimentAPI.py` after activating the environment. The API runs on **port 5001**, so it can run alongside the web interface.

| Endpoint | Returns |
| --- | --- |
| `/api/sentiments` | All restaurant sentiment XML |
| `/api/sentiments/<restaurant_name>` | The first matching restaurant entry |
| `/api/sentiments/<restaurant_name>/<aspect_name>` | The first matching aspect entry |

Example: http://127.0.0.1:5001/api/sentiments/Demo%20Cafe/food

Names must match the XML exactly. Unknown names return HTTP 404. Each successful response is validated against the corresponding RelaxNG schema. Generate XML before starting the API. Both Flask servers are intended for local development.

## Original dataset workflow

The academic project used the Zomato restaurant review data referenced in [this Kaggle notebook's input section](https://www.kaggle.com/code/shahules/zomato-complete-eda-and-lstm-model/input). Download `zomato.csv` separately and place it in `Datasets/`. Downloaded data and generated outputs are excluded from Git; only the fictional demo CSV is included.

With the virtual environment active, run:

```bash
python scripts/DataCleaning.py
python scripts/RestaurantAspectSentimentAnalysis.py --input Datasets/cleaned_restaurant_reviews.csv
python scripts/StoreInDatabase.py
python scripts/XMLGeneration.py
```

On Windows, use `.\.venv\Scripts\python.exe` in place of `python` if the environment is not activated. The cleaning script retains a reproducible 10% sample (`random_state=42`), preserves punctuation and case for NLP, and writes `Datasets/cleaned_restaurant_reviews.csv`. Analysis of the larger dataset can take time. An existing subset can also be supplied using `--input`; the script does not create that subset automatically.

## Method and limitations

The sentiment classifier uses [VADER's documented thresholds](https://github.com/cjhutto/vaderSentiment#about-the-scoring): positive at scores of at least `0.05`, negative at scores of at most `-0.05`, and neutral between those values. A restaurant/aspect label is derived from its mean score, so the displayed label agrees with that score. The code uses the `vaderSentiment` package directly; no NLTK installation or lexicon download is needed.

Aspect extraction is restricted to the whitelist in `RestaurantAspectSentimentAnalysis.py`. Every detected aspect within a sentence receives that sentence's score. A sentence such as “The food was great but the service was terrible” therefore cannot reliably assign different sentiments to food and service. Sarcasm, domain-specific language, and mixed opinions can also produce incorrect labels. Averaging can hide disagreement between reviewers. The results are a rule-based approximation of aspect sentiment.

The API identifies restaurants by name and returns the first match, so restaurants sharing a name across locations are ambiguous. Automated accuracy evaluation, a location-aware API, and more precise aspect sentiment modeling are possible future improvements.

## Project structure

```text
Datasets/demo_reviews.csv                  Fictional runnable example
scripts/DataCleaning.py                    Optional original-data preprocessing
scripts/RestaurantAspectSentimentAnalysis.py  Aspect extraction and scoring
scripts/sentiment_utils.py                 VADER score classification
scripts/StoreInDatabase.py                 SQLite generation
scripts/XMLGeneration.py                   XML generation
scripts/RestaurantAspectSentimentAPI.py     Flask XML API (port 5001)
scripts/WebAppRestaurantAnalysis.py        Flask web interface (port 5000)
templates/WebAppRestaurantAnalysis.html     Search form and chart
schemas/                                  RelaxNG schemas
tests/                                    Regression and integration checks
requirements.txt                          Core application dependencies
requirements-scraper.txt                   Optional search-script dependencies
```

`scripts/ScrapeWebPagesIRTM.py` is a separate coursework search experiment about AI and labour markets; it is not used by ReviewLens. Its optional dependencies can be installed with `python -m pip install -r requirements-scraper.txt`.

## Verification

After installing dependencies and the spaCy model:

```bash
python -m unittest discover -s tests -v
```

## References

- Hutto, C. J., & Gilbert, E. (2014). *VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text*. ICWSM. [Code and citation](https://github.com/cjhutto/vaderSentiment).
- [spaCy](https://spacy.io/) for noun chunks, sentence segmentation, and lemmatization.
- [Flask](https://flask.palletsprojects.com/), [pandas](https://pandas.pydata.org/), [Plotly](https://plotly.com/python/), and [lxml](https://lxml.de/) for the application and data pipeline.
- Dataset source: the [Kaggle Zomato notebook input](https://www.kaggle.com/code/shahules/zomato-complete-eda-and-lstm-model/input) referenced by the original project.
