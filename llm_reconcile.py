import json
import os

from dotenv import load_dotenv
from openai import OpenAI

# --------------------------------------------------
# Configuration
# --------------------------------------------------

load_dotenv()

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)

MODEL = os.environ["GROQ_MODEL"]


# --------------------------------------------------
# Analyze Mismatch
# --------------------------------------------------
# def normalize_string(value):

#     if value is None:
#         return None

#     return (
#         str(value)
#         .replace(" ", "")
#         .replace(",", "")
#         .upper()
#         .strip()
#     )

def analyze_mismatch(
    field: str,
    termsheet_value,
    booking_value,
    evidence: str | None,
):
    """
    Use LLM to determine whether the mismatch is:

    - MATCH
    - FALSE_ALERT
    - TRUE_MISMATCH

    Returns:
    {
        "classification": "...",
        "reason": "..."
    }
    """

    prompt = f"""
You are a trade reconciliation analyst.

Your task is to determine whether the detected mismatch
between a term sheet and booking system is:

MATCH
FALSE_ALERT
TRUE_MISMATCH

Definitions:

MATCH
- Values are effectively identical.

FALSE_ALERT
- Values differ only in representation.
- Examples:
  - 10.75% vs 0.1075
  - USD vs US Dollar
  - 50,000,000 vs 50000000
  - 15-Oct-2035 vs 2035-10-15

TRUE_MISMATCH
- Values genuinely differ and require investigation.

Field:
{field}

Term Sheet Value:
{termsheet_value}

Booking Value:
{booking_value}

Evidence Quote:
{evidence}

Return ONLY valid JSON:

{{
  "classification":
      "MATCH"
      | "FALSE_ALERT"
      | "TRUE_MISMATCH",

  "reason": "short explanation"
}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content":
                    "You are an expert bond trade reconciliation analyst.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    try:

        result = json.loads(
            response.choices[0].message.content
        )

        return result

    except Exception as exc:

        return {
            "classification":
                "TRUE_MISMATCH",
            "reason":
                f"Failed to parse LLM response: {exc}",
        }


# --------------------------------------------------
# Process All Mismatches
# --------------------------------------------------

def analyze_reconciliation_results(
    reconciliation_results,
):
    """
    Accepts the output from compare_fields()
    and enriches mismatches using LLM analysis.
    """

    final_results = []

    # for item in reconciliation_results:

    #     status = item["status"]

    #     if status == "MATCH":

    #         final_results.append(item)
    #         continue

    #     analysis = analyze_mismatch(
    #         field=item["field"],
    #         termsheet_value=
    #             item["extracted_value"],
    #         booking_value=
    #             item["booking_value"],
    #         evidence=
    #             item.get("evidence"),
    #     )
    for item in reconciliation_results:

        status = item.get("status")

        if status != "MISMATCH":
            final_results.append(item)
            continue

        analysis = analyze_mismatch(
            field=item.get("field"),
            termsheet_value=item.get(
                "extracted_value"
            ),
            booking_value=item.get(
                "booking_value"
            ),
            evidence=item.get(
                "evidence"
            ),
        )

        final_results.append(
            {
                **item,
                "status":
                    analysis[
                        "classification"
                    ],
                "reason":
                    analysis[
                        "reason"
                    ],
            }
        )

    return final_results


# --------------------------------------------------
# Standalone test
# --------------------------------------------------

if __name__ == "__main__":

    sample = [
        {
            "field": "Coupon",
            "extracted_value": 10.75,
            "booking_value": 0.1075,
            "status": "MISMATCH",
            "evidence":
                "Coupon: 10.75% per annum",
        },
        {
            "field": "Currency",
            "extracted_value": "USD",
            "booking_value": "USD",
            "status": "MATCH",
            "evidence":
                "Currency: USD",
        },
    ]

    result = analyze_reconciliation_results(
        sample
    )

    print(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
    )