import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError

# from schemas import ExtractionResult
# print("Loaded schema fields are:",
#     ExtractionResult.model_json_schema()
# )
# --------------------------------------------------
# Configuration
# --------------------------------------------------
from schemas import CoreExtractionResult
from schemas import (
    ExtendedExtractionResult,
)

load_dotenv()

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)

MODEL = os.environ["GROQ_MODEL"]


# --------------------------------------------------
# Build document text
# --------------------------------------------------

# def build_document_text(pdf_json: dict) -> str:

#     sections = []

#     for page in pdf_json["pages"]:

#         page_text = page.get(
#             "text",
#             "",
#         )

#         sections.append(
#             f"PAGE {page['page']}\n{page_text}"
#         )

#         tables = page.get(
#             "tables",
#             [],
#         )

#         for table in tables:

#             rows = table.get(
#                 "rows",
#                 [],
#             )

#             table_text = "\n".join(
#                 [
#                     " | ".join(
#                         str(cell)
#                         for cell in row
#                     )
#                     for row in rows
#                 ]
#             )

#             sections.append(
#                 f"\nTABLE PAGE {page['page']}\n"
#                 f"{table_text}"
#             )

#     return "\n\n".join(sections)

CORE_FIELDS = [
    "ISIN",
    "Issuer",
    "Maturity",
    "Coupon",
    "Currency",
    "Notional",
    "SettlementDate",
]

EXTENDED_FIELDS = [
    "DayCountFraction",
    "InterestPaymentDate",
    "IssueDate",
    "IssueAmount",
    "IssuePrice",
    "NominalAmountPerBond",
    "InterestPaymentFrequency",
    "BusinessDayConvention",
    "BusinessDayLocation",
    "AmortizationType",
    "MinimumSubscription",
    "Parent",
]

def extract_core_fields(
    document_text,
):
    prompt = f"""
Extract ONLY these fields:

{chr(10).join(CORE_FIELDS)}

For every field return:

{{
  "value": value,
  "evidence": evidence,
  "source_quote": source_quote,
  "page": page,
  "status": "extracted" or "missing"
}}

Return JSON only.

DOCUMENT:

{document_text}
"""

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        max_tokens=700,
        response_format={
            "type": "json_object"
        },
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    parsed = json.loads(
        response.choices[0]
        .message.content
    )

    return (
        CoreExtractionResult
        .model_validate(
            parsed
        )
        .model_dump()
    )

def extract_extended_fields(
    document_text,
):
    prompt = f"""
Extract ONLY these fields:

{chr(10).join(EXTENDED_FIELDS)}

For missing values return:

{{
  "value": null,
  "evidence": null,
  "source_quote": null,
  "page": null,
  "status": "missing"
}}

Return JSON only.

DOCUMENT:

{document_text}
"""

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        max_tokens=700,
        response_format={
            "type": "json_object"
        },
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    parsed = json.loads(
        response.choices[0]
        .message.content
    )

    return (
        ExtendedExtractionResult
        .model_validate(
            parsed
        )
        .model_dump()
    )


def build_document_text(pdf_json: dict) -> str:
    """
    Build a compact document representation.

    Uses:
    - introductory sections
    - tables

    Skips full page text to reduce token usage.
    """

    sections = []

    # Introductory text only

    for intro in pdf_json.get(
        "introductory_sections",
        [],
    ):

        text = intro.get("text", "")

        if text:

            sections.append(
                f"PAGE {intro.get('page')}\n{text}"
            )

    # Tables

    for page in pdf_json.get(
        "pages",
        [],
    ):

        tables = page.get(
            "tables",
            [],
        )

        for table in tables:

            rows = table.get(
                "rows",
                [],
            )

            table_text = "\n".join(
                [
                    " | ".join(
                        str(cell)
                        for cell in row
                    )
                    for row in rows
                ]
            )

            sections.append(
                f"PAGE {page['page']} TABLE\n"
                f"{table_text}"
            )

    result = "\n\n".join(sections)

    # Safety limit
    # print("=" * 60)
    # print(f"Document Length: {len(document_text)} chars")
    # print("=" * 60)

    MAX_CHARS = 8000

    if len(result) > MAX_CHARS:
        result = result[:MAX_CHARS]

    return result

# -----------------------------------
# Generic LLM extraction call
# -----------------------------------

def extract_fields(
    document_text,
    field_list,
):

    fields_text = "\n".join(
        field_list
    )

    prompt = f"""
You are an expert bond term sheet parser.

Extract ONLY these fields:

{fields_text}

For every field return:

{{
  "FieldName": {{
      "value": extracted value,
      "evidence": exact supporting text,
      "source_quote": exact supporting text,
      "page": page number,
      "status": "extracted" | "missing"
  }}
}}

Rules:

- Return valid JSON only.
- No markdown.
- No explanations.
- Use null if value not found.
- source_quote must be copied exactly.
- source_quote must not exceed 100 chars.
- Dates => YYYY-MM-DD.
- Numbers => JSON numbers.

DOCUMENT:

{document_text}
"""

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={
            "type": "json_object"
        },
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    raw = (
        response.choices[0]
        .message.content
    )

    return json.loads(raw)



# --------------------------------------------------
# Main extraction
# --------------------------------------------------

def extract_bond_fields(
    pdf_json: dict,
):
    """
    Calls the LLM and returns validated
    extraction data.

    Returns:
    {
        "ISIN": {...},
        ...
    }
    """
    
    document_text = (
        build_document_text(
            pdf_json
        )
    )
    print(
    f"Document size POST : {len(document_text)} chars"
)

    prompt = f"""
You are an expert fixed-income and bond term sheet parser.

Extract the requested fields from the document.

For EVERY field return:

{{
  "value": extracted value,
  "evidence": exact supporting text,
  "source_quote": exact supporting quote,
  "page": page number,
  "status": "extracted" | "missing"
}}

Rules:

1. Return VALID JSON ONLY.
2. Do not return markdown.
3. Do not return explanations.
4. Do not invent values.
5. If a value is unavailable, use:

{{
  "value": null,
  "evidence": null,
  "source_quote": null,
  "page": null,
  "status": "missing"
}}

6. Coupon, Notional, IssueAmount, IssuePrice,
   NominalAmountPerBond and MinimumSubscription
   must be JSON numbers, not strings.

7. Dates must be returned as YYYY-MM-DD.

8. Extract information from both:
   - narrative text
   - tables

9. Ignore row numbers when interpreting table content.

10. Evidence must support the extracted value.

11. source_quote must be copied exactly from the document.

Evidence Rules:

- evidence must be copied EXACTLY from the document.
- source_quote must be copied EXACTLY from the document.
- Do NOT explain the evidence.
- Do NOT summarize the evidence.
- Do NOT write sentences describing the evidence.
- evidence and source_quote must be direct snippets from the document.
- source_quote must not exceed 100 characters.
- Return the shortest exact quote supporting the extracted value.
- If no exact quote exists, return null.

Page Rules:

- page must indicate where the evidence was found.
- Use the actual document page number.
- If uncertain, set page to null.

Required Fields:

ISIN
Issuer
Maturity
Notional
Coupon
Currency
SettlementDate
DayCountFraction
InterestPaymentDate
IssueDate
IssueAmount
IssuePrice
NominalAmountPerBond
InterestPaymentFrequency
BusinessDayConvention
BusinessDayLocation
AmortizationType
MinimumSubscription
Parent

Expected JSON Structure:

{{
  "ISIN": {{
    "value": "...",
    "evidence": "...",
    "source_quote": "...",
    "page": 1,
    "status": "extracted"
  }},
  "Issuer": {{
    "value": "...",
    "evidence": "...",
    "source_quote": "...",
    "page": 1,
    "status": "extracted"
  }}
}}

DOCUMENT:

{document_text}
"""

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        max_tokens=600,
        response_format={
            "type": "json_object"
        },
        messages=[
            {
                "role": "system",
                "content":
                    "You are a bond term sheet extraction engine. Return valid JSON only.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    raw = (
        response.choices[0]
        .message.content
    )
    print("\n====== RAW RESPONSE ======\n")
    print(raw) 
    parsed = json.loads(raw)

    print("parsed k",parsed.keys())
    core_result = extract_fields(
        document_text,
        CORE_FIELDS,
    )

    validated_core = (
        CoreExtractionResult
        .model_validate(core_result)
    )
    extended_result = extract_fields(
        document_text,
        EXTENDED_FIELDS,
    )

    validated_extended = (
        ExtendedExtractionResult
        .model_validate(extended_result)
    )
    final_result = {
        **validated_core.model_dump(
            mode="json"
        ),
        **validated_extended.model_dump(
            mode="json"
        ),
    }
    return final_result
    # try:

    #     validated = (
    #         ExtractionResult
    #         .model_validate_json(raw)
    #     )

    #     return (
    #         validated.model_dump(
    #             mode="json"
    #         )
    #     )

    # except ValidationError as exc:

    #     raise ValueError(
    #         f"Schema validation failed:\n{exc}"
    #     )


# --------------------------------------------------
# Local Test
# --------------------------------------------------

if __name__ == "__main__":

    from pathlib import Path

    sample_file = Path(
        "output/sample_raw_text.json"
    )

    pdf_json = json.loads(
        sample_file.read_text(
            encoding="utf-8"
        )
    )

    result = extract_bond_fields(
        pdf_json
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )