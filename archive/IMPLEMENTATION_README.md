# Implementation Guide

Read this file from top to bottom. The project has two ways to run:

- `python quick_test.py` - quick test, starts services, runs demo, stops services.
- `python start_services.py` - keeps services running so you can open Swagger UI.

## 1. Install

Open PowerShell:

```powershell
cd "H:\My Drive\SEM2 ASSIGNMENT\SEML\seml-ecommerce-reco"
python -m pip install -r requirements.txt
```

## 2. Quick Test

Run this first:

```powershell
python quick_test.py
```

This command does everything automatically:

1. Starts the recommendation service.
2. Starts the API gateway.
3. Sends three user activity events.
4. Requests top-5 recommendations.
5. Saves output in `evidence/`.
6. Stops both services.

If it works, you will see:

```text
Demo completed successfully.
```

You will also see a recommendation response like:

```json
{
  "user_id": "u7",
  "strategy": "item-based-collaborative-filtering",
  "recommendations": [
    {"item_id": "P28", "score": 10.027},
    {"item_id": "P25", "score": 9.243}
  ],
  "served_by": "api-gateway",
  "pattern": "api-gateway"
}
```

## 3. Keep Services Running

Use this when you want to open Swagger UI:

```powershell
python start_services.py
```

It prints URLs like:

```text
Gateway Swagger UI: http://127.0.0.1:8000/docs
Internal service Swagger UI: http://127.0.0.1:8001/docs
```

Open those URLs in your browser.

Stop the services with:

```text
Ctrl+C
```

## 4. Test While Services Are Running

In a second PowerShell window:

```powershell
cd "H:\My Drive\SEM2 ASSIGNMENT\SEML\seml-ecommerce-reco"
python demo_requests.py
```

The demo client sends activity events to the gateway and then asks for recommendations.

## 5. Manual API Test

Only use this if you want to test one endpoint yourself.

```powershell
$headers = @{ Authorization = "Bearer seml-demo-token" }

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/activity" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body '{"user_id":"u7","item_id":"P03","action":"click"}'
```

Then:

```powershell
$headers = @{ Authorization = "Bearer seml-demo-token" }

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/recommend?user_id=u7&k=5" `
  -Headers $headers
```

## 6. What Each File Does

| File | Meaning |
|---|---|
| `recommender_engine.py` | Recommendation logic and user-item matrix |
| `recommendation_api.py` | Internal service with event queue and recommender endpoint |
| `api_gateway.py` | Public API gateway |
| `demo_requests.py` | Simple test client |
| `report_evidence.py` | Creates plot and metric evidence |
| `quick_test.py` | Quick full test |
| `start_services.py` | Starts both services and keeps them running |

## 7. How the Architecture Works

```text
Client
  -> API Gateway
      -> Recommendation Service
          -> Event Queue
          -> Feature Store
          -> Recommendation Logic
```

Two assignment patterns are visible:

1. API Gateway: the client calls the gateway, not the internal service.
2. Event-Driven Architecture: activity events go into a queue and are processed by a background consumer.

## 8. How Recommendation Works

The code uses item-based collaborative filtering.

Simple version:

1. User actions become weights.

```text
view = 1
click = 2
cart = 3
purchase = 5
```

2. The system stores those weights in a user-item matrix.
3. It computes item similarity using cosine similarity.
4. It scores unseen products for the user.
5. It returns top-5 recommendations.

## 9. Generate Report Evidence

Run:

```powershell
python report_evidence.py
```

This updates:

```text
evidence/offline_metrics.json
evidence/sample_output.txt
evidence/recommendation_output_plot.png
```

## 10. Common Problems

### Port already in use

Use:

```powershell
python quick_test.py
```

or:

```powershell
python start_services.py
```

Both scripts pick free ports automatically.

### Unauthorized

Use this header:

```text
Authorization: Bearer seml-demo-token
```

### Too many requests

Wait one second and retry.

### Swagger URL does not open

Use `python start_services.py`, not `python quick_test.py`.

`quick_test.py` stops services after testing.  
`start_services.py` keeps services open.

## 11. Final Check

Before showing the implementation, run:

```powershell
python -m py_compile recommender_engine.py recommendation_api.py api_gateway.py demo_requests.py report_evidence.py quick_test.py start_services.py
python quick_test.py
python report_evidence.py
```


