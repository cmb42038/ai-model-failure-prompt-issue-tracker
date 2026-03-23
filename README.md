# AI Model Failure - Prompt Issue Tracker

A beginner-friendly Python project for collecting and organizing messy AI bug reports.

This first milestone sets up a small FastAPI application and a basic test so the project has a clean foundation for future work like report normalization, clustering, and similarity search.

## Project Structure

```text
app/
  __init__.py
  main.py
tests/
  test_main.py
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

## Run Tests

```powershell
pytest
```

## Current Milestone

Right now the project includes:

- a minimal FastAPI app
- a basic pytest test
- a simple project structure
- setup instructions for local development
