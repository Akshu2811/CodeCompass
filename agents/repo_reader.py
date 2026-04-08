import time
from tools.github_tool import fetch_repo_tree, fetch_file_content
from agents.code_mapper import map_code
from db.database import set_job_status

# Limit extensions for faster demo ingestions
SUPPORTED_EXTENSIONS = ('.py', '.js', '.ts', '.html', '.md', '.go', '.java', '.cpp', '.rs', '.json', '.txt')

import asyncio

async def ingest_repository(repo_url: str):
    """
    Fetches the repository, walks its code files, and applies the code_mapper to populate SQLite.
    This runs in the background.
    """
    set_job_status(repo_url, "in_progress")
    try:
        tree, branch, repo_path, headers = fetch_repo_tree(repo_url)
        processed_count = 0
        
        for item in tree:
            if item["type"] == "blob" and item["path"].endswith(SUPPORTED_EXTENSIONS):
                raw_url = f"https://raw.githubusercontent.com/{repo_path}/{branch}/{item['path']}"
                content = fetch_file_content(raw_url, headers)
                
                # Exclude enormous compiled or minified artifacts
                if content and len(content) < 100000:
                    await map_code(repo_url, item["path"], content)
                    processed_count += 1
                
                # Rate limiting for APIs lightly
                await asyncio.sleep(1.0)

        set_job_status(repo_url, "completed")
    except Exception as e:
        import traceback
        print(f"Error ingesting repository {repo_url}: {e}")
        with open("ingest_error.txt", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        set_job_status(repo_url, "failed")
