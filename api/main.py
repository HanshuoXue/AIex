from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def home():
    return {"ok": True}

@app.get("/healthz")
def healthz():
    return {"status": "ok"}