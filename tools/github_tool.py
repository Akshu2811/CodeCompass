import requests
import os

def fetch_repo_tree(repo_url: str):
    """Fetches the repository file tree structure recursively using GitHub API."""
    repo_path = repo_url.replace("https://github.com/", "").strip("/")
    token = os.getenv("GITHUB_TOKEN", "").strip()
    headers = {"Authorization": f"token {token}"} if token else {}
    
    # fetch default branch
    url = f"https://api.github.com/repos/{repo_path}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    default_branch = resp.json().get("default_branch", "main")
    
    # fetch tree recursively
    tree_url = f"https://api.github.com/repos/{repo_path}/git/trees/{default_branch}?recursive=1"
    tree_resp = requests.get(tree_url, headers=headers)
    tree_resp.raise_for_status()
    return tree_resp.json().get("tree", []), default_branch, repo_path, headers

def fetch_file_content(download_url_path: str, headers: dict) -> str:
    """Fetches raw file content."""
    resp = requests.get(download_url_path, headers=headers)
    if resp.status_code == 200:
        return resp.text
    return ""
