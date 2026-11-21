import os
import shutil
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from google.genai import errors
from pydantic import BaseModel, Field

from app.database import get_connection, init_db, list_documents
from app.embedder import get_model
from app.ingest_service import ingest_pdf
from app.rag import answer_question

UPLOAD_DIR = "data"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with get_connection() as conn:
        init_db(conn)
    get_model()  # load the embedding model now, not on the first request
    yield


app = FastAPI(title="RAG Bot API", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    k: int = Field(default=5, ge=1, le=10)


class Source(BaseModel):
    filename: str
    page: int
    content: str
    distance: float


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/documents")
def documents():
    with get_connection() as conn:
        return list_documents(conn)


@app.post("/upload")
def upload(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a .pdf file.")

    safe_name = os.path.basename(file.filename)
    destination = os.path.join(UPLOAD_DIR, safe_name)
    with open(destination, "wb") as out:
        shutil.copyfileobj(file.file, out)

    try:
        return ingest_pdf(destination)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    try:
        return answer_question(request.question, k=request.k)
    except errors.APIError:
        raise HTTPException(
            status_code=503, detail="The AI service is busy. Please try again shortly."
        )