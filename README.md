## Overview

AI Product Catalogue Intelligence is a Python-based application designed to automate product information extraction and SEO content generation from product catalogue screenshots.

The application combines Optical Character Recognition (OCR), image analysis, web research, and locally run AI models to transform product listings into structured catalogue data.

## Key Features

- **Product Detection:** Identifies individual product cards from catalogue screenshots arranged in a grid.
- **Text Extraction:** Uses Tesseract OCR to extract visible product names, pricing information, and other text.
- **AI-Powered Product Identification:** Uses the locally running Moondream model through Ollama to interpret product images and identify product details.
- **Web-Based Enrichment:** Searches for additional product information and extracts relevant content from webpages where available.
- **SEO Keyword Generation:** Generates primary keywords, secondary keywords, long-tail keywords, and buyer search terms tailored to individual products.
- **Catalogue Content Generation:** Produces product descriptions, listing titles, SEO titles, meta descriptions, attributes, and tags.
- **Structured Output:** Organizes extracted information into a format suitable for catalogue review and export.
- **Interactive Interface:** Uses Streamlit to provide a user-friendly interface for uploading screenshots and reviewing analysis results.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | Interactive web interface |
| Tesseract OCR | Text extraction from product images |
| Pillow | Image processing and product-card cropping |
| Ollama | Local AI model execution |
| Moondream | Visual product identification and AI-generated content |
| Beautiful Soup | Webpage content extraction |
| Requests | HTTP requests for product research |
| DuckDuckGo Search | Online product information discovery |
| Pandas | Tabular data handling and export |

## How It Works

1. **Upload:** The user uploads a screenshot containing multiple product listings.
2. **Detect:** The image is divided into individual product cards based on the configured grid.
3. **Extract:** OCR identifies the visible text within each product card.
4. **Identify:** The local vision model helps identify the product name, brand, and category.
5. **Research:** The application searches for additional product information online.
6. **Generate:** AI produces structured catalogue content and product-specific SEO keyword suggestions.
7. **Review and Export:** The results are presented in Streamlit for review and can be exported for further use.

## Limitations

- Product-card detection currently relies on a configured row-and-column grid.
- OCR accuracy depends on image quality, text size, and screenshot resolution.
- AI-generated descriptions and keywords may contain errors and require human review.
- Online research depends on network connectivity and website accessibility.
- Generated keywords are suggestions; actual search volume, keyword difficulty, and ranking performance are not measured.
- Product prices, discounts, ingredients, and claims should be verified against reliable sources before publication.

## Project Status

This project is a prototype exploring the application of local AI, OCR, web research, and SEO content generation to ecommerce catalogue workflows.
<img width="959" height="454" alt="ss1" src="https://github.com/user-attachments/assets/2d18f13c-5948-44ab-b949-48d4aba5755c" />
<img width="955" height="458" alt="ss2" src="https://github.com/user-attachments/assets/91b9726f-f79d-4ce4-a1b1-9be1efaa127c" />


