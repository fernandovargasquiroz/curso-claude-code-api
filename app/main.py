from fastapi import FastAPI

from app.states import list_states

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/states")
def states() -> list[dict[str, int | str]]:
    return [{"id": state.id, "code": state.code} for state in list_states()]
