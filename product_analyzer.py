
import io
import json
import re

import ollama
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from PIL import Image


MODEL_NAME = "moondream:latest"


def run_moondream(prompt, image_bytes=None):
    """Run the local Moondream model."""
    kwargs = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "options": {
            "num_ctx": 4096,
            "temperature": 0,
            "num_predict": 500,
        },
    }

    if image_bytes is not None:
        kwargs["images"] = [image_bytes]

    response = ollama.generate(**kwargs)
    return response.get("response", "").strip()


def identify_product(image_bytes, ocr_text):
    """Identify the product from its image and OCR text."""
    prompt = f"""
Identify the main product in the image.

Text extracted from image:
{ocr_text[:500]}

Return exactly three lines:
Product: product name
Brand: brand name
Type: product category

Do not invent details. Use Unknown if uncertain.
"""

    try:
        text = run_moondream(prompt, image_bytes)
    except Exception:
        text = ""

    result = {
        "product_name": "",
        "brand": "",
        "product_type": "",
    }

    for line in text.splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()

        if key == "product":
            result["product_name"] = value
        elif key == "brand":
            result["brand"] = value
        elif key == "type":
            result["product_type"] = value

    if not result["product_name"]:
        result["product_name"] = ocr_text[:100].strip() or "Unknown"

    if not result["brand"]:
        match = re.search(r"\b(Foxtale)\b", ocr_text, re.I)
        result["brand"] = match.group(1) if match else "Unknown"

    if not result["product_type"]:
        result["product_type"] = "Unknown"

    return result


def search_product_information(query, max_results=5):
    """Search for relevant product information online."""
    results = []

    try:
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("href", ""),
                    "snippet": item.get("body", ""),
                })
    except Exception as error:
        print(f"Web search failed: {error}")

    return results


def extract_page_content(url):
    """Extract product metadata and text from a webpage."""
    if not url or not url.startswith(("https://", "http://")):
        return {}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        metadata = {}

        for script in soup.find_all(
            "script", type="application/ld+json"
        ):
            try:
                data = json.loads(script.string or script.get_text())
                objects = data if isinstance(data, list) else [data]

                for obj in objects:
                    if not isinstance(obj, dict):
                        continue

                    candidates = obj.get("@graph", [])
                    if not isinstance(candidates, list):
                        candidates = []

                    candidates.append(obj)

                    for candidate in candidates:
                        if not isinstance(candidate, dict):
                            continue

                        schema_type = candidate.get("@type", "")
                        if isinstance(schema_type, list):
                            schema_type = " ".join(schema_type)

                        if "Product" not in str(schema_type):
                            continue

                        brand_data = candidate.get("brand", {})
                        if isinstance(brand_data, dict):
                            brand_data = brand_data.get("name", "")

                        offers = candidate.get("offers", {})
                        if isinstance(offers, list):
                            offers = offers[0] if offers else {}

                        metadata = {
                            "name": candidate.get("name", ""),
                            "description": candidate.get("description", ""),
                            "brand": brand_data,
                            "sku": candidate.get("sku", ""),
                            "price": (
                                offers.get("price")
                                if isinstance(offers, dict)
                                else None
                            ),
                            "currency": (
                                offers.get("priceCurrency")
                                if isinstance(offers, dict)
                                else None
                            ),
                        }
                        break

            except (json.JSONDecodeError, TypeError, AttributeError):
                continue

            if metadata:
                break

        for element in soup.select(
            "script, style, nav, footer, header, noscript, iframe"
        ):
            element.decompose()

        page_text = re.sub(
            r"\s+", " ", " ".join(soup.stripped_strings)
        ).strip()

        return {
            "url": url,
            "title": soup.title.get_text(strip=True) if soup.title else "",
            "metadata": metadata,
            "text": page_text[:4000],
        }

    except requests.RequestException as error:
        print(f"Could not fetch webpage: {error}")
        return {}


def build_keyword_suggestions(
    product_name, brand, product_type, evidence=None
):
    """Generate specific, purchase-oriented SEO keywords."""
    evidence = evidence or []

    name = (product_name or "").strip()
    brand = (brand or "").strip()
    category = (product_type or "").strip()
    research_text = " ".join(map(str, evidence)).lower()

    def clean(items, limit):
        output = []
        seen = set()

        for item in items:
            item = re.sub(r"\s+", " ", str(item)).strip(" -|,")
            if not item or len(item) < 3:
                continue

            key = item.casefold()
            if key not in seen:
                seen.add(key)
                output.append(item)

        return output[:limit]

    ingredient_map = {
        "glycolic acid": ["glycolic acid"],
        "lactic acid": ["lactic acid"],
        "salicylic acid": ["salicylic acid"],
        "niacinamide": ["niacinamide"],
        "hyaluronic acid": ["hyaluronic acid"],
        "ceramides": ["ceramide", "ceramides"],
        "vitamin c": ["vitamin c"],
        "retinol": ["retinol"],
        "kojic acid": ["kojic acid"],
        "aloe vera": ["aloe vera"],
        "zinc pca": ["zinc pca"],
    }

    benefit_map = {
        "tan removal": ["de-tan", "detan", "tan removal"],
        "brightening": ["brightening", "brightens", "radiance"],
        "uneven skin tone": ["uneven skin tone", "pigmentation"],
        "acne care": ["acne", "breakouts", "blemishes"],
        "exfoliation": ["exfoliation", "exfoliates", "dead skin"],
        "hydration": ["hydration", "hydrating", "moisturizing"],
        "sun protection": ["sun protection", "sunscreen", "spf"],
        "skin smoothing": ["smooth skin", "smooth texture"],
        "barrier care": ["skin barrier", "barrier repair"],
    }

    ingredients = [
        ingredient
        for ingredient, phrases in ingredient_map.items()
        if any(phrase in research_text for phrase in phrases)
    ]

    benefits = [
        benefit
        for benefit, phrases in benefit_map.items()
        if any(phrase in research_text for phrase in phrases)
    ]

    primary = [
        name,
        f"{brand} {name}" if brand else "",
        f"{brand} {category}" if brand and category else "",
    ]

    secondary = [
        f"buy {name}",
        f"{name} price",
        f"{name} online",
        f"{brand} {category}" if brand and category else "",
        f"{category} online" if category else "",
    ]

    for ingredient in ingredients:
        secondary.extend([
            f"{ingredient} {category}".strip(),
            f"{brand} {ingredient} {category}".strip(),
        ])

    for benefit in benefits:
        secondary.extend([
            f"{benefit} {category}".strip(),
            f"{name} for {benefit}".strip(),
        ])

    long_tail = [
        f"where to buy {name}",
        f"{name} price in India",
        f"{brand} {name} review".strip(),
    ]

    for ingredient in ingredients:
        long_tail.append(f"{category} with {ingredient}".strip())

    for benefit in benefits:
        long_tail.append(f"{category} for {benefit}".strip())

    buyer_terms = [
        f"buy {name} online",
        f"{name} price in India",
        f"where to buy {name}",
        f"{brand} {category} online".strip(),
    ]

    return {
        "primary_keywords": clean(primary, 10),
        "secondary_keywords": clean(secondary, 20),
        "long_tail_keywords": clean(long_tail, 20),
        "buyer_search_terms": clean(buyer_terms, 10),
    }


def parse_json_response(text):
    """Safely parse the model's JSON response."""
    if not text:
        return {}

    cleaned = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        text.strip(),
        flags=re.IGNORECASE,
    )

    try:
        result = json.loads(cleaned)
        return result if isinstance(result, dict) else {}
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group(0))
            return result if isinstance(result, dict) else {}
        except json.JSONDecodeError:
            pass

    return {}


def analyze_product_image(image, ocr_text=""):
    """Research one product and generate its catalogue and SEO data."""
    if not isinstance(image, Image.Image):
        image = Image.open(image)

    image = image.convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()

    product = identify_product(image_bytes, ocr_text)

    query = " ".join(
        value for value in [
            product["brand"],
            product["product_name"],
            product["product_type"],
            ocr_text[:150],
        ]
        if value and value.lower() != "unknown"
    )

    research = search_product_information(query, 5) if query else []
    evidence = []

    for item in research[:4]:
        page = extract_page_content(item.get("url", ""))

        if page:
            item["page_content"] = page.get("text", "")[:1800]
            item["metadata"] = page.get("metadata", {})

            if item["metadata"]:
                evidence.append(
                    json.dumps(item["metadata"], ensure_ascii=False)
                )

            if item["page_content"]:
                evidence.append(item["page_content"])

        if item.get("snippet"):
            evidence.append(item["snippet"])

    prompt = f"""
You are an ecommerce catalogue and SEO specialist.

PRODUCT IDENTIFICATION:
{json.dumps(product, ensure_ascii=False)}

IMAGE OCR TEXT:
{ocr_text[:1500]}

WEB RESEARCH:
{json.dumps(research, ensure_ascii=False)[:7000]}

Return ONLY a valid JSON object with these fields:
{{
  "product_name": "",
  "brand": "",
  "category": "",
  "attributes": [],
  "description": "",
  "listing_title": "",
  "seo_title": "",
  "meta_description": "",
  "primary_keywords": [],
  "secondary_keywords": [],
  "long_tail_keywords": [],
  "tags": [],
  "buyer_search_terms": [],
  "price": null,
  "discount": null,
  "source_urls": [],
  "uncertain_details": []
}}

Instructions:
- Prefer verified product-page information over guesses.
- Do not invent ingredients, benefits, prices, discounts or specifications.
- Include price and discount only when explicitly verified.
- Make SEO keywords specific to this product and buyer intent.
- Use ingredients and benefits only when supported by the evidence.
- Make the listing title descriptive and readable.
- Keep SEO title concise and meta description under 160 characters.
- State uncertain details in uncertain_details.
- Return valid JSON only, without Markdown.
"""

    try:
        response = run_moondream(prompt)
        result = parse_json_response(response)
    except Exception as error:
        print(f"Catalogue generation failed: {error}")
        result = {}

    # Fill missing fields safely.
    defaults = {
        "product_name": product["product_name"],
        "brand": product["brand"],
        "category": product["product_type"],
        "attributes": [],
        "description": "",
        "listing_title": "",
        "seo_title": "",
        "meta_description": "",
        "primary_keywords": [],
        "secondary_keywords": [],
        "long_tail_keywords": [],
        "tags": [],
        "buyer_search_terms": [],
        "price": None,
        "discount": None,
        "source_urls": [],
        "uncertain_details": [],
    }

    for key, default in defaults.items():
        if result.get(key) is None:
            result[key] = default

    for key in [
        "attributes",
        "primary_keywords",
        "secondary_keywords",
        "long_tail_keywords",
        "tags",
        "buyer_search_terms",
        "source_urls",
        "uncertain_details",
    ]:
        if not isinstance(result.get(key), list):
            result[key] = []

    # Add URLs that were actually searched.
    result["source_urls"] = list(dict.fromkeys(
        result["source_urls"] + [
            item["url"] for item in research if item.get("url")
        ]
    ))

    # Add evidence-informed keywords without removing model suggestions.
    keywords = build_keyword_suggestions(
        result["product_name"],
        result["brand"],
        result["category"],
        evidence,
    )

    for key in [
        "primary_keywords",
        "secondary_keywords",
        "long_tail_keywords",
        "buyer_search_terms",
    ]:
        result[key] = list(dict.fromkeys(
            result[key] + keywords[key]
        ))

    if not result["listing_title"]:
        result["listing_title"] = (
            f"{result['brand']} {result['product_name']}".strip()
        )

    if not result["seo_title"]:
        result["seo_title"] = result["listing_title"][:60]

    if not result["meta_description"]:
        result["meta_description"] = (
            f"Explore {result['product_name']} by {result['brand']}. "
            "View product details and features."
        )[:160]

    if result["price"] is None:
        result["uncertain_details"].append("Price not verified.")

    if result["discount"] is None:
        result["uncertain_details"].append("Discount not verified.")

    result["uncertain_details"] = list(dict.fromkeys(
        result["uncertain_details"]
    ))

    return json.dumps(result, indent=2, ensure_ascii=False)
