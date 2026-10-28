import json
from pathlib import Path

from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException,
)

from booking_parser import (
    load_booking_file,
)

from read_pdf import (
    extract_pdf,
)

from llm_extract import (
    extract_bond_fields,
)

from reconcile import (
    compare_fields,
)

from llm_reconcile import (
    analyze_reconciliation_results,
)

app = FastAPI(
    title="Bond Trade Reconciliation API",
    version="1.0.0",
)


UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("output")

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


@app.get("/")
def health():

    return {
        "status": "running",
        "service": "Bond Reconciliation API",
    }


@app.post("/reconcile")
async def reconcile_trade(
    pdf_file: UploadFile = File(...),
    booking_file: UploadFile = File(...),
):

    try:

        # ----------------------------------
        # Save uploaded files
        # ----------------------------------

        pdf_path = (
            UPLOAD_DIR / pdf_file.filename
        )

        booking_path = (
            UPLOAD_DIR / booking_file.filename
        )

        pdf_path.write_bytes(
            await pdf_file.read()
        )

        booking_path.write_bytes(
            await booking_file.read()
        )

        print(
            f"PDF uploaded: {pdf_path}"
        )

        print(
            f"Booking uploaded: {booking_path}"
        )

        # ----------------------------------
        # STEP 1
        # Extract PDF
        # ----------------------------------

        print(
            "\nSTEP 1: Extracting PDF..."
        )

        pdf_content = extract_pdf(
            pdf_path
        )

        # ----------------------------------
        # STEP 2
        # Core + Extended LLM Extraction
        # ----------------------------------

        print(
            "\nSTEP 2: Running LLM Extraction..."
        )

        extraction_result = (
            extract_bond_fields(
                pdf_content
            )
        )

        extraction_file = (
            OUTPUT_DIR
            / f"{pdf_path.stem}_extraction.json"
        )

        extraction_file.write_text(
            json.dumps(
                extraction_result,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        # ----------------------------------
        # STEP 3
        # Read booking extract
        # ----------------------------------

        print(
            "\nSTEP 3: Loading Booking..."
        )

        booking_record = (
            load_booking_file(
                booking_path
            )
        )

        booking_output = (
            OUTPUT_DIR
            / f"{pdf_path.stem}_booking.json"
        )

        booking_output.write_text(
            json.dumps(
                booking_record,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        # ----------------------------------
        # STEP 4
        # Initial Comparison
        # ----------------------------------

        print(
            "\nSTEP 4: First Pass Reconciliation..."
        )

        first_pass_results = (
            compare_fields(
                extraction_result,
                booking_record,
            )
        )

        first_pass_file = (
            OUTPUT_DIR
            / f"{pdf_path.stem}_first_pass.json"
        )

        first_pass_file.write_text(
            json.dumps(
                first_pass_results,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        # ----------------------------------
        # STEP 5
        # LLM False Alert Analysis
        # ----------------------------------

        print(
            "\nSTEP 5: False Alert Analysis..."
        )

        reconciliation_results = (
            analyze_reconciliation_results(
                first_pass_results
            )
        )

        # ----------------------------------
        # Final Report
        # ----------------------------------

        report = {
            "pdf":
                pdf_file.filename,
            "booking":
                booking_file.filename,
            "results":
                reconciliation_results,
        }

        final_report_file = (
            OUTPUT_DIR
            / f"{pdf_path.stem}_final_report.json"
        )

        final_report_file.write_text(
            json.dumps(
                report,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        print(
            f"\nFinal report saved: "
            f"{final_report_file}"
        )

        return report

    except Exception as exc:

        print(
            f"\nERROR: {str(exc)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )