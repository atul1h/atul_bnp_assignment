import json
from pathlib import Path

import pandas as pd


BOOKING_FIELD_MAPPING = {
    "tradeid": "TradeID",
    "isin": "ISIN",
    "issuer": "Issuer",
    "maturity": "Maturity",
    "notional": "Notional",
    "coupon": "Coupon",
    "currency": "Currency",
    "settlementdate": "SettlementDate",
    "daycountfraction": "DayCountFraction",
    "interestpaymentdate": "InterestPaymentDate",
    "issuedate": "IssueDate",
    "issueamount": "IssueAmount",
    "issueprice": "IssuePrice",
    "nominalamountperbond": "NominalAmountPerBond",
    "interestpaymentfrequency":
        "InterestPaymentFrequency",
    "businessdayconvention":
        "BusinessDayConvention",
    "amortizationtype":
        "AmortizationType",
    "minimumsubscription":
        "MinimumSubscription",
    "parent":
        "Parent",
}


def normalize_columns(record: dict):

    normalized = {}

    for key, value in record.items():

        clean_key = (
            str(key)
            .replace("_", "")
            .replace(" ", "")
            .lower()
        )

        mapped_key = (
            BOOKING_FIELD_MAPPING.get(
                clean_key,
                key,
            )
        )

        normalized[mapped_key] = value

    return normalized


def load_booking_file(file_path: Path):

    suffix = file_path.suffix.lower()

    if suffix == ".csv":

        df = pd.read_csv(file_path)

        if df.empty:
            raise ValueError(
                "Booking CSV is empty."
            )

        record = (
            df.iloc[0]
            .to_dict()
        )

        return normalize_columns(
            record
        )

    if suffix == ".json":

        content = json.loads(
            file_path.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(content, list):

            if len(content) == 0:
                raise ValueError(
                    "Booking JSON empty."
                )

            content = content[0]

        return normalize_columns(
            content
        )

    raise ValueError(
        f"Unsupported booking file type: {suffix}"
    )