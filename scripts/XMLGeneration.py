import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Load your CSV or DataFrame
df = pd.read_csv(ROOT / "Datasets/restaurant_aspect_sentiments.csv")

# Create root element
root = ET.Element("restaurantSentiments")

# Group data by restaurant and location
grouped = df.groupby(['restaurant', 'location'])

for (restaurant, location), group in grouped:
    rest_elem = ET.SubElement(root, "restaurant", name=restaurant, location=location)
    for _, row in group.iterrows():
        aspect_elem = ET.SubElement(rest_elem, "aspect", name=row['aspect'])
        sentiment_elem = ET.SubElement(aspect_elem, "sentiment", score=str(round(row['sentiment_score'], 4)))
        sentiment_elem.text = row['sentiment']

# Save to XML file
tree = ET.ElementTree(root)

xml_str = ET.tostring(root, encoding='utf-8')
parsed = minidom.parseString(xml_str)
pretty_xml_as_str = parsed.toprettyxml(indent="  ")

# Save to file
with open(ROOT / "restaurant_sentiments.xml", "w", encoding="utf-8") as f:
    f.write(pretty_xml_as_str)

print(" Pretty XML saved as restaurant_sentiments.xml")
