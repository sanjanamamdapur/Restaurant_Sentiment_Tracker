import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Google search query
query = '"macroeconomic impact" AI "labor market" OECD quantitative since 2018'
google_url = "https://www.google.com/search"

# Parameters
params = {
    "q": query,
    "num": 20,
    "hl": "en"
}

# Headers to mimic a browser
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}

# Send request
response = requests.get(google_url, headers=headers, params=params)
soup = BeautifulSoup(response.text, "html.parser")

results = []
rank = 1

# Parse search results
for item in soup.select("div.tF2Cxc")[:20]:
    title_tag = item.select_one("h3")
    link_tag = item.select_one("a")

    if title_tag and link_tag:
        title = title_tag.get_text()
        url = link_tag["href"]

        results.append({
            "Rank": rank,
            "Title": title,
            "URL": url
        })
        rank += 1

# Create DataFrame
df = pd.DataFrame(results)

# Save to Excel
output_file = "macroeconomic_AI_labor_market_OECD.xlsx"
df.to_excel(output_file, index=False)

print(f"Saved {len(df)} results to {output_file}")
