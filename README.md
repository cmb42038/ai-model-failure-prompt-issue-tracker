# AI Model Failure / Prompt Issue Tracker

A beginner-friendly Python project for collecting messy AI bug reports, turning them into cleaner incident records, and evaluating a few simple baseline workflows around them.

The project is intentionally small and practical. It is meant to be understandable, easy to extend, and useful as a foundation for future work such as better retrieval, richer normalization, or embeddings-based analysis.

## What This Project Does

This repository provides a small FastAPI backend that can:

- accept raw AI bug reports
- normalize those reports into a cleaner incident format
- retrieve similar incidents with a TF-IDF plus cosine similarity baseline
- group incidents into rough failure-pattern clusters
- draft reproduction cases with a local fallback and an optional LLM path
- run a small benchmark over the current baseline behavior

## Why It Matters

AI bug reports are often inconsistent. Different people describe the same issue in different ways, and that makes it harder to compare failures, find repeats, prioritize work, or build better datasets later.

This project focuses on the early steps of that workflow:

- capture the report
- normalize the information
- compare it with related incidents
- group rough patterns
- produce a draft repro case
- evaluate the current baseline

## Current Features

- `POST /bug-reports` stores raw bug reports in memory
- `POST /bug-reports/normalize` converts a raw report into a normalized incident
- `POST /incidents/similar` returns top similar incidents from a small sample corpus plus current in-memory reports
- `GET /incidents/clusters` returns rough failure-pattern groupings
- `POST /bug-reports/repro-draft` creates a repro-case draft from a raw bug report
- `POST /incidents/repro-draft` creates a repro-case draft from a normalized incident
- `python -m app.evaluation` runs the small baseline benchmark

## Project Structure

```text
app/
  clustering.py
  evaluation.py
  __init__.py
  main.py
  normalization.py
  repro.py
  retrieval.py
  schemas.py
  data/
    evaluation_cases.json
    sample_incidents.json
tests/
  test_bug_reports.py
  test_clustering.py
  test_evaluation.py
  test_main.py
  test_normalization.py
  test_repro.py
  test_retrieval.py
.env.example
requirements.txt
README.md
```

## Installation

1. Create a virtual environment:

```powershell
python -m venv .venv
```

2. Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Optional: copy the environment example if you want to try the repro-drafting API path:

```powershell
Copy-Item .env.example .env
```

If you do that, update the values in `.env` before enabling real API calls.

## Run The API

Start the development server:

```powershell
uvicorn app.main:app --reload
```

Useful URLs:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

## Example API Usage

The easiest way to explore the API is through the FastAPI docs page at `/docs`. If you want to send requests directly from PowerShell, this is a simple example payload:

```powershell
$body = @{
  title = "Model ignored system instruction"
  model_name = "gpt-4.1-mini"
  prompt = "Summarize this support ticket in one sentence."
  expected_behavior = "Return a one-sentence summary."
  actual_behavior = "Returned a long bulleted list instead."
  tags = @("formatting", "instruction-following")
} | ConvertTo-Json
```

Store a raw bug report:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/bug-reports" `
  -ContentType "application/json" `
  -Body $body
```

Normalize the same report:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/bug-reports/normalize" `
  -ContentType "application/json" `
  -Body $body
```

Find similar incidents:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/incidents/similar" `
  -ContentType "application/json" `
  -Body $body
```

Get rough incident clusters:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/incidents/clusters"
```

Draft a repro case:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/bug-reports/repro-draft" `
  -ContentType "application/json" `
  -Body $body
```

## Run Tests

```powershell
pytest
```

## Run The Evaluation / Benchmark

Run the baseline benchmark with:

```powershell
python -m app.evaluation
```

The benchmark uses the labeled sample dataset in `app/data/evaluation_cases.json` and reports simple checks for:

- normalization structure and expected labels
- top-1 similar-incident retrieval
- clustering pairwise group agreement
- repro-case draft completeness

## Current Limitations

- raw bug report storage is in memory only, so data is lost when the app restarts
- normalization is rule-based and intentionally simple
- retrieval and clustering use small TF-IDF baselines, not embeddings
- the sample datasets are small and hand-written
- repro drafting falls back to a local rule-based generator unless LLM use is explicitly enabled
- the live API path for repro drafting was not exercised in automated tests
- evaluation metrics are basic and designed for clarity, not exhaustive measurement

## Future Improvements

- persistent storage for reports and normalized incidents
- richer incident schemas and stronger normalization rules
- embeddings-based retrieval and clustering
- better benchmark coverage and larger labeled datasets
- more robust evaluation for generated repro drafts
- optional UI or reporting layer once the backend foundations are stable
