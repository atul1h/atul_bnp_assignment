

from datetime import date
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
)


class FieldEvidence(BaseModel):

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
    )

    value: object | None

    evidence: str | None

    source_quote: str | None

    page: int | None

    status: Literal[
        "extracted",
        "missing",
    ]

class CoreExtractionResult(BaseModel):

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
    )

    ISIN: FieldEvidence
    Issuer: FieldEvidence
    Maturity: FieldEvidence
    Notional: FieldEvidence
    Coupon: FieldEvidence
    Currency: FieldEvidence
    SettlementDate: FieldEvidence

class ExtendedExtractionResult(BaseModel):

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
    )

    DayCountFraction: FieldEvidence
    InterestPaymentDate: FieldEvidence
    IssueDate: FieldEvidence
    IssueAmount: FieldEvidence
    IssuePrice: FieldEvidence
    NominalAmountPerBond: FieldEvidence
    InterestPaymentFrequency: FieldEvidence
    BusinessDayConvention: FieldEvidence
    BusinessDayLocation: FieldEvidence
    AmortizationType: FieldEvidence
    MinimumSubscription: FieldEvidence
    Parent: FieldEvidence
    
# class ExtractionResult(BaseModel):

#     model_config = ConfigDict(
#         strict=True,
#         extra="forbid",
#     )

#     ISIN: FieldEvidence
#     Issuer: FieldEvidence
#     Maturity: FieldEvidence
#     Notional: FieldEvidence
#     Coupon: FieldEvidence
#     Currency: FieldEvidence
#     SettlementDate: FieldEvidence


# class ExtendedExtraction(BaseModel):
#     model_config = ConfigDict(
#         strict=True,
#         extra="forbid",
#     )

#     DayCountFraction: FieldEvidence
#     InterestPaymentDate: FieldEvidence
#     IssueDate: FieldEvidence
#     IssueAmount: FieldEvidence
#     IssuePrice: FieldEvidence
#     NominalAmountPerBond: FieldEvidence
#     InterestPaymentFrequency: FieldEvidence
#     BusinessDayConvention: FieldEvidence
#     BusinessDayLocation: FieldEvidence
#     AmortizationType: FieldEvidence
#     MinimumSubscription: FieldEvidence
#     Parent: FieldEvidence