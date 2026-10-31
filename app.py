
import io
import json

import pandas as pd
import streamlit as st
from PIL import Image

from product_grouping import group_text_by_product
from product_analyzer import analyze_product_image


st.set_page_config(
    page_title="AI Product Catalogue Intelligence",
    page_icon="📦",
    layout="wide",
)

st.title("📦 AI Product Catalogue Intelligence")
st.caption(
    "Upload a product catalogue screenshot to extract product information "
    "and generate product-specific SEO keywords."
)

with st.sidebar:
    st.header("Analysis settings")

    rows = st.number_input(
        "Number of product rows",
        min_value=1,
        max_value=20,
        value=3,
        step=1,
    )

    columns = st.number_input(
        "Products per row",
        min_value=1,
        max_value=20,
        value=3,
        step=1,
    )

    max_products = st.number_input(
        "Maximum products to analyse",
        min_value=1,
        max_value=400,
        value=100,
        step=1,
    )

    st.info(
        "Set the row and column counts to match your screenshot. "
        "Every product card in that grid will be processed."
    )

uploaded = st.file_uploader(
    "Upload a product catalogue screenshot",
    type=["png", "jpg", "jpeg", "webp"],
)

if uploaded:
    try:
        image = Image.open(uploaded).convert("RGB")
    except Exception as exc:
        st.error(f"Unable to open the image: {exc}")
        st.stop()

    left, right = st.columns([1, 1])

    with left:
        st.subheader("Uploaded screenshot")
        st.image(image, use_container_width=True)
        st.caption(f"Image dimensions: {image.width} × {image.height}")

    with right:
        st.subheader("What you'll receive")
        st.markdown(
            """
            - Product name, brand and category
            - Product attributes and description
            - Primary SEO keywords
            - Secondary and long-tail keywords
            - Buyer search terms and tags
            - Listing title and meta description
            - Research sources and uncertain details
            """
        )

        st.warning(
            "Review product names, categories and generated keywords "
            "before publishing. Search volume is not measured."
        )

    run = st.button(
        "Analyse all products",
        type="primary",
        use_container_width=True,
    )

    if run:
        st.session_state.pop("catalogue_results", None)

        with st.spinner("Detecting product cards..."):
            try:
                detected_products = group_text_by_product(
                    image,
                    rows=int(rows),
                    columns=int(columns),
                )
            except Exception as exc:
                st.error(f"Product detection failed: {exc}")
                st.stop()

        if not detected_products:
            st.warning("No product cards were detected.")
            st.stop()

        detected_products = detected_products[:int(max_products)]

        st.info(
            f"Found {len(detected_products)} product card(s) to analyse."
        )

        results = []
        progress = st.progress(0)
        status = st.empty()

        for index, product in enumerate(detected_products):
            product_number = index + 1

            status.write(
                f"Analysing product {product_number} "
                f"of {len(detected_products)}..."
            )

            try:
                raw_result = analyze_product_image(
                    product["Image"],
                    ocr_text=product.get("Extracted Text", ""),
                )

                if isinstance(raw_result, str):
                    data = json.loads(raw_result)
                else:
                    data = raw_result

                if not isinstance(data, dict):
                    raise ValueError(
                        "The analyser did not return a valid product object."
                    )

                data["product_number"] = product_number
                data["ocr_text"] = product.get("Extracted Text", "")
                data["analysis_status"] = "Completed"

            except Exception as exc:
                data = {
                    "product_number": product_number,
                    "product_name": "Analysis failed",
                    "brand": "",
                    "category": "",
                    "description": "",
                    "listing_title": "",
                    "seo_title": "",
                    "meta_description": "",
                    "primary_keywords": [],
                    "secondary_keywords": [],
                    "long_tail_keywords": [],
                    "buyer_search_terms": [],
                    "tags": [],
                    "attributes": [],
                    "price": None,
                    "discount": None,
                    "source_urls": [],
                    "uncertain_details": [str(exc)],
                    "ocr_text": product.get("Extracted Text", ""),
                    "analysis_status": "Failed",
                }

            results.append(data)
            progress.progress(product_number / len(detected_products))

        st.session_state["catalogue_results"] = results
        status.success("Product analysis finished.")

    results = st.session_state.get("catalogue_results", [])

    if results:
        st.divider()
        st.subheader("Catalogue results")

        completed = sum(
            1 for item in results
            if item.get("analysis_status") == "Completed"
        )

        metric1, metric2, metric3 = st.columns(3)

        metric1.metric("Products processed", len(results))
        metric2.metric("Successful analyses", completed)
        metric3.metric("Failed analyses", len(results) - completed)

        table_rows = []

        for item in results:
            table_rows.append({
                "Product Number": item.get("product_number", ""),
                "Status": item.get("analysis_status", ""),
                "Product Name": item.get("product_name", ""),
                "Brand": item.get("brand", ""),
                "Category": item.get("category", ""),
                "Description": item.get("description", ""),
                "Listing Title": item.get("listing_title", ""),
                "SEO Title": item.get("seo_title", ""),
                "Meta Description": item.get("meta_description", ""),
                "Primary Keywords": ", ".join(
                    map(str, item.get("primary_keywords", []))
                ),
                "Secondary Keywords": ", ".join(
                    map(str, item.get("secondary_keywords", []))
                ),
                "Long-tail Keywords": ", ".join(
                    map(str, item.get("long_tail_keywords", []))
                ),
                "Buyer Search Terms": ", ".join(
                    map(str, item.get("buyer_search_terms", []))
                ),
                "Tags": ", ".join(
                    map(str, item.get("tags", []))
                ),
                "Attributes": ", ".join(
                    map(str, item.get("attributes", []))
                ),
                "Price": item.get("price"),
                "Discount": item.get("discount"),
                "Source URLs": ", ".join(
                    map(str, item.get("source_urls", []))
                ),
                "Uncertain Details": "; ".join(
                    map(str, item.get("uncertain_details", []))
                ),
                "OCR Text": item.get("ocr_text", ""),
            })

        df = pd.DataFrame(table_rows)

        st.caption(
            "You can edit the table before exporting. "
            "Each row represents one product."
        )

        edited_df = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            key="catalogue_editor",
        )

        csv_data = edited_df.to_csv(index=False).encode("utf-8-sig")

        excel_buffer = io.BytesIO()

        with pd.ExcelWriter(
            excel_buffer,
            engine="openpyxl",
        ) as writer:
            edited_df.to_excel(
                writer,
                index=False,
                sheet_name="Product Catalogue",
            )

            keyword_columns = [
                "Product Number",
                "Product Name",
                "Brand",
                "Primary Keywords",
                "Secondary Keywords",
                "Long-tail Keywords",
                "Buyer Search Terms",
            ]

            edited_df[keyword_columns].to_excel(
                writer,
                index=False,
                sheet_name="SEO Keywords",
            )

        download1, download2 = st.columns(2)

        with download1:
            st.download_button(
                "Download CSV",
                data=csv_data,
                file_name="product_catalogue.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with download2:
            st.download_button(
                "Download Excel",
                data=excel_buffer.getvalue(),
                file_name="product_catalogue.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                use_container_width=True,
            )

        st.divider()
        st.subheader("Individual product details")

        for item in results:
            product_name = item.get("product_name", "Unknown product")
            product_number = item.get("product_number", "?")

            with st.expander(
                f"Product {product_number}: {product_name}"
            ):
                st.write("**Brand:**", item.get("brand") or "Unknown")
                st.write("**Category:**", item.get("category") or "Unknown")
                st.write(
                    "**Description:**",
                    item.get("description") or "Not available",
                )
                st.write(
                    "**Listing title:**",
                    item.get("listing_title") or "Not available",
                )
                st.write(
                    "**SEO title:**",
                    item.get("seo_title") or "Not available",
                )
                st.write(
                    "**Meta description:**",
                    item.get("meta_description") or "Not available",
                )

                st.markdown("**Primary keywords**")
                st.write(item.get("primary_keywords", []))

                st.markdown("**Secondary keywords**")
                st.write(item.get("secondary_keywords", []))

                st.markdown("**Long-tail keywords**")
                st.write(item.get("long_tail_keywords", []))

                st.markdown("**Buyer search terms**")
                st.write(item.get("buyer_search_terms", []))

                st.markdown("**Research sources**")
                sources = item.get("source_urls", [])

                if sources:
                    for source in sources:
                        st.markdown(f"- [{source}]({source})")
                else:
                    st.write("No sources retrieved.")

                if item.get("uncertain_details"):
                    st.warning(
                        "Review notes: "
                        + "; ".join(
                            str(detail)
                            for detail in item.get("uncertain_details", [])
                            if detail is not None and str(detail).lower() != "nan"
                        )
                    )

                if item.get("ocr_text"):
                   st.markdown("**Extracted image text:**"):
                   st.write(item["ocr_text"])

else:
    st.info(
        "Upload a screenshot to begin. Set its row and column counts "
        "in the sidebar, then analyse all product cards."
    )

st.divider()

st.caption(
    "AI-generated product details and SEO suggestions require human review. "
    "Keyword search volume and ranking difficulty are not measured."
)
