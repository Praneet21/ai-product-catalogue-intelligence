
import pytesseract
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def extract_text_from_image(image, min_confidence=20):
    """Extract text and coordinates from an image or card crop."""

    if not isinstance(image, Image.Image):
        image = Image.open(image)

    image = image.convert("RGB")

    # Enlarge small card text for better OCR recognition.
    scale = 3
    image = image.resize(
        (image.width * scale, image.height * scale),
        Image.Resampling.LANCZOS,
    )

    # Improve contrast while retaining the original text shapes.
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)
    image = ImageEnhance.Contrast(image).enhance(1.4)
    image = image.filter(ImageFilter.SHARPEN)

    data = pytesseract.image_to_data(
        image,
        output_type=pytesseract.Output.DICT,
        config="--oem 3 --psm 11",
    )

    results = []

    for i, raw_text in enumerate(data["text"]):
        text = raw_text.strip()

        try:
            confidence = float(data["conf"][i])
        except (ValueError, TypeError):
            continue

        if not text or confidence < min_confidence:
            continue

        results.append(
            {
                "text": text,
                "confidence": round(confidence, 2),
                "x": data["left"][i] // scale,
                "y": data["top"][i] // scale,
                "width": max(1, data["width"][i] // scale),
                "height": max(1, data["height"][i] // scale),
            }
        )

    return results
