
from PIL import Image
from ocr_extractor import extract_text_from_image


def group_text_by_product(image, rows=3, columns=3, padding=5):
    """
    Split a catalogue screenshot into card regions and
    extract text from each card independently.

    Accepts a PIL Image or an image file path.
    """
    if not isinstance(image, Image.Image):
        image = Image.open(image)

    image = image.convert("RGB")
    width, height = image.size

    products = []

    for row in range(rows):
        for column in range(columns):
            left = round(column * width / columns) + padding
            top = round(row * height / rows) + padding
            right = round((column + 1) * width / columns) - padding
            bottom = round((row + 1) * height / rows) - padding

            card = image.crop((left, top, right, bottom))
            text_items = extract_text_from_image(card)

            # Preserve the text's reading order.
            text_items.sort(
                key=lambda item: (item["y"], item["x"])
            )

            products.append(
                {
                    "Product Number": len(products) + 1,
                    "Extracted Text": " ".join(
                        item["text"] for item in text_items
                    ),
                    "Items": text_items,
                    "Image": card,
                }
            )

    return products
