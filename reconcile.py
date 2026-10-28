# reconcile.py

# from schemas import (
#     CoreExtraction,
#     ExtendedExtraction,
# )
from datetime import date


def normalize_value(value):
    """
    Normalize values before comparison.
    """

    if isinstance(value, date):
        return value.isoformat()

    return value


def compare_fields(
    extracted: dict,
    booking: dict,
):
    """
    First-pass reconciliation.

    Returns:
        MATCH
        MISMATCH

    MISMATCH values will later be sent
    to llm_reconcile.py for False Alert /
    True Mismatch analysis.
    """

    results = []

    for field, booking_value in booking.items():

        extracted_field = extracted.get(field)

        if extracted_field is None:

            results.append({
                "field": field,
                "status": "FIELD_NOT_EXTRACTED",
            })

            continue

        extracted_value = extracted_field.get(
            "value"
        )

        extracted_value = normalize_value(
            extracted_value
        )

        booking_value = normalize_value(
            booking_value
        )

        if extracted_value == booking_value:

            status = "MATCH"

        else:

            status = "MISMATCH"

        results.append(
            {
                "field": field,
                "status": status,
                "extracted_value":
                    extracted_value,
                "booking_value":
                    booking_value,
                "evidence":
                    extracted_field.get(
                        "source_quote"
                    ),
                "page":
                    extracted_field.get(
                        "page"
                    ),
            }
        )

    return results


def get_mismatches(
    reconciliation_results,
):
    """
    Returns only mismatches.
    These will be sent to the
    second LLM pass.
    """

    return [
        item
        for item in reconciliation_results
        if item["status"] == "MISMATCH"
    ]
