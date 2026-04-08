import os
import vertexai
vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT", "code-compass-agent"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
)
import re
# trigger reload
from fastapi import FastAPI, BackgroundTasks, APIRouter, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(override=True)


app = FastAPI(title="CodeCompass Central API")

# Setup DB upon app boot
init_db()

router = APIRouter()

class IngestRequest(BaseModel):
    repo_url: str

class AskRequest(BaseModel):
    repo_url: str
    question: str

@router.post("/ingest")
async def ingest_codebase(request: IngestRequest, background_tasks: BackgroundTasks):
    github_pattern = re.compile(
        r'^https://github\.com/[\w.-]+/[\w.-]+/?$'
    )
    if not github_pattern.match(request.repo_url):
        raise HTTPException(
            status_code=400,
            detail="Invalid URL. Only GitHub repository URLs are accepted. Format: https://github.com/owner/repo"
        )

    URL = request.repo_url

    status = get_job_status(URL)
    if status in ["in_progress", "completed"]:
        return {"status": status, "repo": URL}

    # Trigger background crawling
    background_tasks.add_task(ingest_repository, URL)
    return {"status": "ingestion_started", "repo": URL}

@router.get("/status")
async def check_ingestion_status(repo_url: str):
    # Used for polling long workflows
    return {"status": get_job_status(repo_url), "repo": repo_url}

@router.post("/ask")
async def ask_codebase(request: AskRequest):
    # Wait for natural language query execution context via QA Agent
    answer = await answer_question(request.repo_url, request.question)
    return {"answer": answer}

@router.get("/guide")
async def generate_guide(repo_url: str):
    # Try fetching existing path
    conn = get_connection()
    row = conn.execute("SELECT guide_text FROM onboarding_paths WHERE repo_url = ?", (repo_url,)).fetchone()
    conn.close()
    
    if row:
        return {"guide": row['guide_text']}

    # Create new guide using Pro Agent
    guide = await generate_onboarding_guide(repo_url)
    return {"guide": guide}

@router.get("/modules")
async def list_modules(repo_url: str):
    modules = get_all_modules(repo_url)
    output = [{"path": mod["path"], "summary": mod["summary"]} for mod in modules]
    return {"modules": output}

app.include_router(router)

# Mount frontend
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
    
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
