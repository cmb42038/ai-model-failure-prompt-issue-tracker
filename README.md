# AI Model Failure - Prompt Issue Tracker

A beginner-friendly Python project for collecting and organizing messy AI bug reports.

The project currently includes a small FastAPI application, a Pydantic bug report schema, and basic tests. It is designed to stay simple while building a foundation for future work like normalization, clustering, and similarity search.

## Project Structure

```text
app/
  __init__.py
  main.py
  normalization.py
  schemas.py
tests/
  test_bug_reports.py
  test_main.py
  test_normalization.py
requirements.txt
README.md
```

## Setup

1. Create a virtual environment:

```powershell
python -m venv .venv
```

2. Activate the virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

3. Install the dependencies:

```powershell
pip install -r requirements.txt
```

## Run The App

Start the FastAPI development server:

```powershell
uvicorn app.main:app --reload
```

Then open:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

## Submit A Bug Report

Use the FastAPI docs page at `http://127.0.0.1:8000/docs` or send a `POST` request to `/bug-reports`.

Example JSON body:

```json
{
  "title": "Model ignored system instruction",
  "model_name": "gpt-4.1-mini",
  "prompt": "Summarize this support ticket in one sentence.",
  "expected_behavior": "Return a one-sentence summary.",
  "actual_behavior": "Returned a long bulleted list instead.",
  "tags": ["formatting", "instruction-following"]
}
```

For now, bug reports are stored only in memory. That means they are cleared whenever the app restarts.

## Normalize A Bug Report

Send the same bug report JSON to `POST /bug-reports/normalize` to get a cleaner incident format back.

The normalization logic is intentionally simple for now. It uses straightforward rules such as:

- trimming extra whitespace
- lowercasing and cleaning tags
- assigning a basic issue type from keywords
- building a short summary

This keeps the code easy to understand before adding any real LLM-based processing later.

## Run Tests

```powershell
pytest
```

## Current Milestone

Right now the project includes:

- a minimal FastAPI app
- a Pydantic bug report schema
- a POST endpoint for bug reports
- a normalized incident layer
- a simple normalization service
- basic pytest tests
- a simple project structure
- setup instructions for local development
