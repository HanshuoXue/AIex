from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def root():
    return {"status": "alive", "message": "Simple API working"}

@app.get("/env")
def env():
    return {
        "AZURE_OPENAI_KEY": "SET" if os.environ.get("AZURE_OPENAI_KEY") else "NOT SET",
        "AZURE_OPENAI_ENDPOINT": os.environ.get("AZURE_OPENAI_ENDPOINT", "NOT SET"),
        "working_dir": os.getcwd()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
