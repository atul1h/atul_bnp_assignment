Automated Trade Reconciliation System
The Automated Trade Reconciliation System automates the comparison of financial trade details extracted from term sheets against records maintained in a booking system.

The application uses document parsing, Large Language Model (LLM)-based information extraction, structured data validation, and deterministic reconciliation rules to identify discrepancies between the source term sheet and the booking record.

Key Features

Upload term sheet PDF documents and booking system extracts through FastAPI endpoints.

Extract structured trade attributes using an LLM.

Validate extracted data against a canonical trade schema.

Compare term sheet values with booking system values.

Identify matches, genuine mismatches, and extraction failures.

Capture supporting evidence and page references where available.

Generate a structured JSON reconciliation report.

Support API-based execution and integration with other applications.

2. Technology Stack

Language: Python

API framework: FastAPI

API server: Uvicorn

API documentation and testing: Swagger UI

LLM integration: Groq API, if configured in the application

Document processing: PDF parsing and other configured document libraries

Data validation: Pydantic

Input formats: PDF term sheets and the configured booking extract format

Output format: JSON reconciliation report

Exact package versions are documented in requirements.txt.

3. Project Workflow

The application follows this workflow:

The user uploads a term sheet document through a FastAPI endpoint.

The user uploads the corresponding booking system extract.

The application parses the term sheet and extracts trade attributes.

The extracted fields are validated against the canonical schema.

The booking system extract is loaded and normalized.

The reconciliation module compares the corresponding trade attributes.

The application generates a field-level reconciliation report.

The report is saved in the output/ directory.



Installation and Setup

Step 1: Clone the repository

git clone 


Step 2: Create a virtual environment

On Windows:

python -m venv .venv
.venv\Scripts\activate

Step 3: Install dependencies

python -m pip install --upgrade pip
pip install -r requirements.txt

Step 4: Configure environment variables

Copy .env.example to .env and configure the required values.

Example .env configuration:

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=your_configured_model_name

Starting the FastAPI Application

From the repository root, activate the virtual environment and run:

python -m uvicorn app:app --reload

This command assumes that app.py defines the FastAPI instance as app.

If your application instance or module has a different name, update the command accordingly.

After starting the server, open Swagger UI in your browser:

http://127.0.0.1:8000/docs


Executing the Reconciliation Workflow

Step 1: Open Swagger UI

Navigate to:

http://127.0.0.1:8000/docs

Step 2: Upload the term sheet

Locate the document-upload endpoint, click Try it out, select the term sheet PDF, and execute the request.

Step 3: Upload the booking system extract

Locate the booking-upload endpoint, select the corresponding booking extract, and execute the request.

The accepted file format and required parameters depend on the endpoint implementation.

Step 4: Execute reconciliation

Use the reconciliation endpoint to process the uploaded files, if reconciliation is exposed separately.

If your upload endpoint automatically triggers reconciliation, execute that endpoint according to the API design.

Step 5: Retrieve the output

After successful processing, inspect the output/ directory in the project folder.

The generated JSON report contains the source filenames and field-level reconciliation results.

The exact endpoint paths, request parameters, and report filenames are defined by the application's implementation.

9. Reconciliation Report

The output is a structured JSON report containing the input filenames and the comparison result for each trade attribute. 
sample report is also present in output folder.

Deliverables

FastAPI application and supporting Python modules.

Dependency configuration.

Environment variable template.

Sample input files, where permitted.

Structured reconciliation reports.
