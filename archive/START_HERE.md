# Start Here

Use this file if you only want to run and test the project.

## Quick Test

```powershell
cd "H:\My Drive\SEM2 ASSIGNMENT\SEML\seml-ecommerce-reco"
python -m pip install -r requirements.txt
python quick_test.py
```

If you see `Demo completed successfully.`, the implementation works.

## Open Swagger UI

```powershell
python start_services.py
```

Then open the URLs printed in the terminal.

Stop with `Ctrl+C`.

## Main Files

| File | Purpose |
|---|---|
| `recommender_engine.py` | Recommendation algorithm |
| `recommendation_api.py` | Internal recommendation API |
| `api_gateway.py` | Public API gateway |
| `demo_requests.py` | Sends demo requests |
| `quick_test.py` | One-command smoke test |
| `start_services.py` | Keeps APIs running for Swagger |

## Build Final Files

```powershell
python build_submission_notebook.py
python build_docx_report.py
python build_pdf_report.py
```

Final files are saved in `..\final_submission\`.

Before upload, replace `GXXX`, group member names, BITS IDs, and contribution percentages.
