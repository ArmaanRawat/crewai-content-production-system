from fastapi import FastAPI

app = FastAPI(title="CrewAI Content Production System")

@app.get("/")
def home():
    return {"message": "Backend is running successfully"}