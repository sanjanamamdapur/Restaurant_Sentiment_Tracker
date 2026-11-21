from flask import Flask, Response, abort
from lxml import etree
from pathlib import Path

app = Flask(__name__)

ROOT = Path(__file__).resolve().parents[1]
XML_FILE = ROOT / "restaurant_sentiments.xml"
SCHEMAS = {
    "full": ROOT / "schemas/restaurant_sentiments_full.rng",
    "restaurant": ROOT / "schemas/restaurant_only.rng",
    "aspect": ROOT / "schemas/aspect_only.rng"
}

def validate_with_relaxng(xml_str, schema_path):
    try:
        relaxng_doc = etree.parse(schema_path)
        relaxng = etree.RelaxNG(relaxng_doc)
        doc = etree.fromstring(xml_str.encode('utf-8'))
        if not relaxng.validate(doc):
            raise ValueError(f"XML validation failed: {relaxng.error_log}")
    except Exception as e:
        raise ValueError(f"Validation error: {str(e)}")

@app.route('/')
def home():
    return "🍽️ Restaurant Sentiment API with RelaxNG XML Validation"

@app.route('/api/sentiments', methods=['GET'])
def get_full_xml():
    try:
        with open(XML_FILE, 'r', encoding='utf-8') as f:
            xml_data = f.read()
        validate_with_relaxng(xml_data, SCHEMAS["full"])
        return Response(xml_data, mimetype='application/xml')
    except Exception as e:
        abort(500, description=str(e))

@app.route('/api/sentiments/<restaurant_name>', methods=['GET'])
def get_sentiment_by_restaurant(restaurant_name):
    try:
        tree = etree.parse(XML_FILE)
        root = tree.getroot()
        match = root.xpath(".//restaurant[@name=$name]", name=restaurant_name)
        if not match:
            return Response(f"<error>No data found for {restaurant_name}</error>", mimetype='application/xml', status=404)
        xml_str = etree.tostring(match[0], pretty_print=True, encoding="unicode")
        validate_with_relaxng(xml_str, SCHEMAS["restaurant"])
        return Response(xml_str, mimetype='application/xml')
    except Exception as e:
        abort(500, description=str(e))

@app.route('/api/sentiments/<restaurant_name>/<aspect_name>', methods=['GET'])
def get_sentiment_for_aspect(restaurant_name, aspect_name):
    try:
        tree = etree.parse(XML_FILE)
        root = tree.getroot()
        xpath_expr = ".//restaurant[@name=$restaurant]/aspect[@name=$aspect]"
        match = root.xpath(xpath_expr, restaurant=restaurant_name, aspect=aspect_name)
        if not match:
            return Response(f"<error>No sentiment data found for '{aspect_name}' in '{restaurant_name}'</error>", mimetype='application/xml', status=404)
        xml_str = etree.tostring(match[0], pretty_print=True, encoding="unicode")
        validate_with_relaxng(xml_str, SCHEMAS["aspect"])
        return Response(xml_str, mimetype='application/xml')
    except Exception as e:
        abort(500, description=str(e))

if __name__ == '__main__':
    app.run(port=5001)
