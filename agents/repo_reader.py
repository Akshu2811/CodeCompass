import os
import vertexai
vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT", "code-compass-agent"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
)
import time
from tools.github_tool import fetch_repo_tree, fetch_file_content
from agents.code_mapper import map_code
from db.database import set_job_status, set_job_progress

# Limit extensions for faster demo ingestions
SUPPORTED_EXTENSIONS = ('.py', '.js', '.ts', '.html', '.md', '.go', '.java', '.cpp', '.rs', '.json', '.txt')

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", "target", "vendor",
    "coverage", ".gradle", ".mvn",
}

SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".mp4", ".mp3", ".pdf", ".zip", ".tar", ".gz",
    ".jar", ".class", ".pyc", ".pyo", ".lock",
}

MAX_FILE_SIZE_BYTES = 100000
MAX_FILES_PER_REPO = 150

import asyncio


def should_skip_file(path: str, size: int = 0) -> bool:
    parts = path.replace("\\", "/").split("/")
    if any(segment in SKIP_DIRS for segment in parts):
        return True
    _, ext = os.path.splitext(path)
    if ext.lower() in SKIP_EXTENSIONS:
        return True
    if size > MAX_FILE_SIZE_BYTES:
        return True
    return False


async def ingest_repository(repo_url: str):
    """
    Fetches the repository, walks its code files, and applies the code_mapper to populate SQLite.
    This runs in the background.
    """
    set_job_status(repo_url, "in_progress")
    try:
        tree, branch, repo_path, headers = fetch_repo_tree(repo_url)
        processed_count = 0

        candidates = [
            item for item in tree
            if item["type"] == "blob"
            and item["path"].endswith(SUPPORTED_EXTENSIONS)
            and not should_skip_file(item["path"], item.get("size", 0))
        ]

        if len(candidates) > MAX_FILES_PER_REPO:
            print(f"Warning: {repo_url} has {len(candidates)} eligible files; truncating to {MAX_FILES_PER_REPO}.")
            candidates = candidates[:MAX_FILES_PER_REPO]

        total = len(candidates)
        for i, item in enumerate(candidates):
            raw_url = f"https://raw.githubusercontent.com/{repo_path}/{branch}/{item['path']}"
            content = fetch_file_content(raw_url, headers)

            if content and len(content) < MAX_FILE_SIZE_BYTES:
                await map_code(repo_url, item["path"], content)
                processed_count += 1

            if total > 0 and (i + 1) % 10 == 0:
                set_job_progress(repo_url, int((i + 1) / total * 100))

            # Rate limiting for APIs lightly
            await asyncio.sleep(1.0)

        set_job_progress(repo_url, 100)
        set_job_status(repo_url, "completed")
    except Exception as e:
        import traceback
        print(f"Error ingesting repository {repo_url}: {e}")
        with open("ingest_error.txt", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        set_job_status(repo_url, "failed")
