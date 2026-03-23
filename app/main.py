from fastapi import FastAPI

app = FastAPI(title="AI Model Failure / Prompt Issue Tracker")


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "project": "AI Model Failure / Prompt Issue Tracker",
        "status": "running",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
