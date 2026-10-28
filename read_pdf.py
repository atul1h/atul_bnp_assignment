
import json
import re
from pathlib import Path

import fitz  # PyMuPDF


# --------------------------------------------------
# Configuration
# --------------------------------------------------

PDF_PATH = Path("4TermSheet _Genel Energy.pdf")
OUTPUT_DIR = Path("output")


# --------------------------------------------------
# Clean extracted text without losing paragraphs
# --------------------------------------------------

def clean_pdf_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Normalize horizontal whitespace but preserve newlines.
    text = re.sub(r"[^\S\n]+", " ", text)

    # Reduce excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# --------------------------------------------------
# Extract tables while preserving original row/column
# structure. Do not assume fixed label/value columns.
# --------------------------------------------------

def extract_tables(page) -> dict:
    extracted_tables = []
    detection_errors = []

    # Try line-based detection first, then text-based detection.
    for strategy in ("lines", "text"):
        try:
            finder = page.find_tables(strategy=strategy)
            detected_tables = list(finder.tables)

            if detected_tables:
                for table_index, table in enumerate(
                    detected_tables, start=1
                ):
                    rows = table.extract()

                    extracted_tables.append({
                        "table_index": table_index,
                        "bbox": [
                            round(float(coord), 2)
                            for coord in table.bbox
                        ],
                        "rows": [
                            [
                                cell.strip() if cell else ""
                                for cell in row
                            ]
                            for row in rows
                        ],
                    })

                # Use the first strategy that finds tables.
                break

        except Exception as exc:
            detection_errors.append(
                f"{strategy}: {type(exc).__name__}: {exc}"
            )

    return {
        "tables": extracted_tables,
        "table_detection_error": (
            "; ".join(detection_errors)
            if detection_errors and not extracted_tables
            else None
        ),
    }


# --------------------------------------------------
# Find the first table in document order.
# Return the earliest table by page, then vertical
# position, then horizontal position.
# --------------------------------------------------

def find_first_table(pages: list) -> dict | None:
    candidates = []

    for page_data in pages:
        for table in page_data["tables"]:
            bbox = table["bbox"]

            candidates.append({
                "page": page_data["page"],
                "table_index": table["table_index"],
                "bbox": bbox,
            })

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda item: (
            item["page"],
            item["bbox"][1],
            item["bbox"][0],
        ),
    )


# --------------------------------------------------
# Extract introductory text before the first table.
#
# Pages before the table page are included in full.
# On the table page, only text blocks completely
# above the table's top boundary are included.
# --------------------------------------------------

def extract_introductory_sections(
    doc,
    pages: list,
    first_table: dict | None,
) -> list:
    if first_table is None:
        return [{
            "status": "REVIEW_REQUIRED",
            "reason": (
                "No table was detected automatically. "
                "Introductory text could not be identified "
                "reliably."
            ),
            "page": None,
            "text": "",
        }]

    table_page_number = first_table["page"]
    table_top_y = first_table["bbox"][1]

    introductory_sections = []

    for page_data in pages:
        page_number = page_data["page"]

        if page_number < table_page_number:
            # All text on preceding pages comes before
            # the first detected table.
            introductory_sections.append({
                "page": page_number,
                "text": page_data["text"],
            })

        elif page_number == table_page_number:
            page = doc[page_number - 1]
            blocks = page.get_text("blocks", sort=True)

            preceding_blocks = []

            for block in blocks:
                x0, y0, x1, y1, text = block[:5]

                if not text or not text.strip():
                    continue

                # Include blocks fully above the first table.
                if y1 <= table_top_y:
                    preceding_blocks.append({
                        "bbox": [
                            round(float(x0), 2),
                            round(float(y0), 2),
                            round(float(x1), 2),
                            round(float(y1), 2),
                        ],
                        "text": clean_pdf_text(text),
                    })

            introductory_sections.append({
                "page": page_number,
                "text": "\n\n".join(
                    block["text"] for block in preceding_blocks
                ),
                "blocks": preceding_blocks,
            })

            # Stop after reaching the first table.
            break

    return introductory_sections


# --------------------------------------------------
# Main PDF extraction
# --------------------------------------------------

def extract_pdf(pdf_path: Path) -> dict:
    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF file not found: {pdf_path.resolve()}"
        )

    pages = []

    with fitz.open(pdf_path) as doc:
        if doc.is_encrypted:
            raise ValueError(
                "The PDF is encrypted and requires a password."
            )

        for page_number, page in enumerate(doc, start=1):
            raw_text = page.get_text("text", sort=True)
            cleaned_text = clean_pdf_text(raw_text)

            table_result = extract_tables(page)

            pages.append({
                "page": page_number,
                "text": cleaned_text,
                "tables": table_result["tables"],
                "table_detection_error": (
                    table_result["table_detection_error"]
                ),
            })

        first_table = find_first_table(pages)

        introductory_sections = extract_introductory_sections(
            doc=doc,
            pages=pages,
            first_table=first_table,
        )

        result = {
            "file_name": pdf_path.name,
            "page_count": len(doc),
            "first_table": first_table,
            "introductory_sections": introductory_sections,
            "pages": pages,
        }

    return result


# --------------------------------------------------
# Save JSON using a dynamic output filename
# --------------------------------------------------

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    result = extract_pdf(PDF_PATH)

    output_file = (
        OUTPUT_DIR / f"{PDF_PATH.stem}_raw_pdf_text.json"
    )

    output_file.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"PDF processed: {PDF_PATH.name}")
    print(f"Pages: {result['page_count']}")
    print(f"First detected table: {result['first_table']}")
    print(f"Output saved: {output_file.resolve()}")

    print("\n--- Introductory text before first table ---")

    for section in result["introductory_sections"]:
        print(f"\nPage: {section.get('page', 'Unknown')}")

        if section.get("status") == "REVIEW_REQUIRED":
            print(section["reason"])
        else:
            print(section.get("text", ""))

    total_tables = sum(
        len(page["tables"]) for page in result["pages"]
    )

    print(f"\nDetected tables: {total_tables}")


if __name__ == "__main__":
    main()
