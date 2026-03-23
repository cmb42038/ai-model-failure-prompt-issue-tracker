# AI Model Failure - Prompt Issue Tracker

A beginner-friendly Python project for collecting and organizing messy AI bug reports.

The project currently includes a small FastAPI application, a Pydantic bug report schema, and basic tests. It is designed to stay simple while building a foundation for future work like normalization, clustering, and similarity search.

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

4. Optional: enable LLM-based repro drafting:

```powershell
Copy-Item .env.example .env
```

Then update the values in `.env` if you want to turn on real API calls.

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

## Find Similar Incidents

Send a bug report to `POST /incidents/similar` to get the top similar normalized incidents.

The retrieval layer uses a simple TF-IDF plus cosine similarity approach written in plain Python so the logic is easy to read. It compares the normalized query against:

- a small sample incident dataset
- any bug reports stored during the current app session

This keeps the retrieval code modular and makes it easier to swap in embeddings later.

## Group Failure Patterns

Use `GET /incidents/clusters` to group the current incident corpus into rough failure-pattern clusters.

This is a baseline implementation. It:

- uses the normalized incident text
- builds simple TF-IDF vectors
- links incidents when their cosine similarity passes a small threshold
- returns connected groups as rough clusters

It is intentionally simple and designed to be replaced later by better clustering methods or embeddings.

## Draft A Repro Case

You can generate a repro-case draft from either:

- `POST /bug-reports/repro-draft`
- `POST /incidents/repro-draft`

Each draft includes:

- a short summary
- the likely failure type
- reproduction steps
- expected behavior
- actual behavior
- a simple pass/fail test case draft

The repro service is split into three small parts:

- prompt construction
- API calling
- response parsing

If LLM use is disabled or not configured, the app falls back to a local rule-based draft so the feature still works without network access.

### Optional LLM Configuration

This milestone includes an optional OpenAI-compatible chat completion integration for repro drafting.

Environment variables:

- `REPRO_USE_LLM`
- `REPRO_LLM_API_KEY`
- `REPRO_LLM_MODEL`
- `REPRO_LLM_BASE_URL`
- `REPRO_LLM_TIMEOUT_SECONDS`

If `REPRO_USE_LLM` is not set to `true`, the app uses the local fallback draft builder instead.

### Testing Note

The automated tests cover the local fallback logic, prompt building, response parsing, configuration loading, and endpoint behavior without network calls.

The live API path was not exercised in automated tests for this milestone.

## Run The Evaluation

Run the small benchmark with:

```powershell
python -m app.evaluation
```

The evaluation uses the labeled sample dataset in `app/data/evaluation_cases.json` and reports simple baseline checks for:

- normalization structure and expected labels
- top-1 similar-incident retrieval
- clustering pairwise group agreement
- repro-case draft completeness

### Evaluation Limitations

- the benchmark is intentionally small and hand-written
- the metrics are simple counts and rule-based checks
- clustering is checked with pairwise agreement, not advanced clustering scores
- repro drafting checks required sections and shape, not writing quality
- the live LLM API path is not scored by this baseline benchmark

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
- a baseline similar-incident retrieval layer
- a baseline failure-pattern clustering layer
- an optional LLM-powered repro-case drafting layer
- a small baseline evaluation framework and benchmark dataset
- basic pytest tests
- a simple project structure
- setup instructions for local development
