from fastapi import FastAPI

app = FastAPI(title="U-Park API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
