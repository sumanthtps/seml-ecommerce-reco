# SEML Assignment I — E-commerce ML Recommendation

This is the single canonical repository for **AIMLCZG546 — Software
Engineering for Machine Learning, Assignment I (Group 049)**.

It contains:

- an item-based collaborative-filtering ML pipeline;
- separate CQRS command/write and query/read microservices;
- automated tests, static checks, CI, Docker support, and live verification;
- GR4ML Business, Analytics Design, and Data Preparation views; and
- the executed notebook and Word report required for submission.

> Before submission, replace every `TO_FILL` value in
> `submission_details.json`, then regenerate the report and notebook.

## Architecture

The **Command Service** owns interaction writes and model training. Training
produces a versioned, immutable model artifact. The **Query Service** loads that
artifact and serves latency-sensitive top-k recommendation requests without
modifying training data.

```text
Storefront / analyst
        │
        ├── commands ──► Command Service :8101
        │                  ├── interaction event log
        │                  └── ML training pipeline
        │                              │
        │                              ▼
        │                    versioned model artifact
        │                              │
        └── queries ───► Query Service :8102
                                       │
                                       ▼
                              top-5 recommendations
```

## Quick start

Python 3.11 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -e ".[dev,report]"

python scripts/seed_data.py
python scripts/train_and_evaluate.py
```

Start the services in separate terminals:

```bash
# Terminal 1: command/write side
uvicorn ecom_ml.command_service.main:app --port 8101

# Terminal 2: query/read side
uvicorn ecom_ml.query_service.main:app --port 8102
```

Run the HTTP demonstration:

```bash
python scripts/run_demo.py
```

API documentation is available at:

- Command Service: <http://127.0.0.1:8101/docs>
- Query Service: <http://127.0.0.1:8102/docs>

For a one-command end-to-end check that starts and stops both services:

```bash
python scripts/verify_live.py
```

## Quality checks

```bash
ruff check src tests scripts tools
ruff format --check src tests scripts tools
mypy --cache-dir=/tmp/seml-mypy-cache
pytest --cov=ecom_ml --cov-report=term-missing
```

The same checks run in GitHub Actions for Python 3.11 and 3.12. Common commands
are also available through `make help`.

## Regenerating assignment artifacts

```bash
python scripts/verify_live.py
python tools/generate_assets.py
python tools/build_report.py
python tools/build_notebook.py
```

To additionally generate a PDF:

```bash
python tools/build_report.py --with-pdf
```

## Repository structure

```text
src/ecom_ml/          Application and ML source code
tests/                Unit and service tests
scripts/              Seed, train, demo, and live-verification commands
tools/                Diagram, report, and notebook generators
data/                 Reproducible interaction dataset
artifacts/            Versioned model and metadata used by the demo
evidence/             GR4ML diagrams and execution evidence
final_submission/     Submission-ready Group 049 files
submission_details.json
```

## Submission files

- `final_submission/G049.ipynb`
- `final_submission/G049_SEML_Assignment_01_Complete_Report.docx`

Only these two files need to be selected when the portal requests the notebook
and report. The rest of the repository exists for reproducibility and review.
