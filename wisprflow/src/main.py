from fastapi import FastAPI

app = FastAPI(title="Wisprflow API")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Wisprflow API"}
