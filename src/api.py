from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from rag import ask

app = FastAPI(title="HR Policy Assistant")

# Demo users aur unke groups (server pe rakhe hai, user badal nahi sakta)
# Production me ye Entra ID login token se aate hai
USERS = {
    "ravi": ["all"],          # normal employee
    "priya": ["all", "hr"],   # HR team
}


class Question(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask_question(body: Question, x_user: str = Header(...)):
    # Header me aaye user ka naam se uske groups nikalo
    groups = USERS.get(x_user.strip().lower())
    if groups is None:
        raise HTTPException(status_code=401, detail="Unknown user")

    result = ask(body.question, groups)
    result["user"] = x_user
    return result