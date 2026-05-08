import os
import json
import re
import httpx
from google import genai
from google.genai import types
from db.database import get_all_modules

_PR_URL_RE = re.compile(
    r"^https://github\.com/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)/pull/(?P<number>\d+)/?$"
)

_client = genai.Client(
    vertexai=True,
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
)

_MODEL = "gemini-2.5-flash"

_SYSTEM_PROMPT = """You are a code review expert. Analyze the provided code and return ONLY valid JSON with no markdown fences, no explanation, no extra text — just the raw JSON object.

The JSON must have exactly this shape:
{
  "overall_score": <integer 0-100>,
  "grade": "<A|B|C|D|F>",
  "summary": "<2-3 sentence assessment>",
  "language": "<detected language>",
  "categories": {
    "code_quality": { "score": <integer 0-100>, "label": "Code Quality" },
    "security": { "score": <integer 0-100>, "label": "Security" },
    "performance": { "score": <integer 0-100>, "label": "Performance" },
    "maintainability": { "score": <integer 0-100>, "label": "Maintainability" },
    "error_handling": { "score": <integer 0-100>, "label": "Error Handling" }
  },
  "issues": [
    { "severity": "CRITICAL|WARNING|SUGGESTION", "title": "...", "description": "...", "fix": "..." }
  ],
  "positives": ["...", "..."]
}

Severity levels:
- CRITICAL: bugs, security vulnerabilities, data loss risks
- WARNING: bad practices, performance problems, potential bugs
- SUGGESTION: style improvements, readability, minor optimizations

Return ONLY the JSON object. No markdown, no explanation."""


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


async def review_code(code: str, language_hint: str = "", extra_system_note: str = "") -> dict:
    user_content = code
    if language_hint:
        user_content = f"Language: {language_hint}\n\n{code}"

    system_prompt = _SYSTEM_PROMPT
    if extra_system_note:
        system_prompt = f"{_SYSTEM_PROMPT}\n\n{extra_system_note}"

    response = await _client.aio.models.generate_content(
        model=_MODEL,
        contents=user_content,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.2,
        ),
    )

    raw = response.text or ""
    cleaned = _strip_fences(raw)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "overall_score": 0,
            "grade": "F",
            "summary": raw,
            "language": language_hint or "unknown",
            "categories": {
                "code_quality": {"score": 0, "label": "Code Quality"},
                "security": {"score": 0, "label": "Security"},
                "performance": {"score": 0, "label": "Performance"},
                "maintainability": {"score": 0, "label": "Maintainability"},
                "error_handling": {"score": 0, "label": "Error Handling"},
            },
            "issues": [
                {
                    "severity": "CRITICAL",
                    "title": "Review failed",
                    "description": "Could not parse model response as JSON.",
                    "fix": "Check raw model output in the summary field.",
                }
            ],
            "positives": [],
        }


async def fetch_and_review_pr(pr_url: str) -> dict:
    match = _PR_URL_RE.match(pr_url.strip())
    if not match:
        raise ValueError(
            f"Invalid PR URL format. Expected: https://github.com/{{owner}}/{{repo}}/pull/{{number}}"
        )

    owner = match.group("owner")
    repo = match.group("repo")
    number = match.group("number")

    token = os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/files"

    async with httpx.AsyncClient() as client:
        response = await client.get(api_url, headers=headers)

    if response.status_code == 401:
        raise PermissionError("GitHub API returned 401: unauthorized. Check that GITHUB_TOKEN is set and has access to this repo.")
    if response.status_code == 404:
        raise FileNotFoundError(f"PR not found (404): {owner}/{repo}#{number}. The repo may be private or the PR number incorrect.")
    response.raise_for_status()

    files = response.json()
    if not files:
        raise ValueError(f"PR {owner}/{repo}#{number} has no file changes (empty diff).")

    changed_filenames = {f.get("filename", "") for f in files if f.get("filename")}

    diff_parts = []
    for f in files:
        filename = f.get("filename", "")
        patch = f.get("patch", "")
        if patch:
            diff_parts.append(f"### {filename}\n{patch}")

    if not diff_parts:
        raise ValueError(f"PR {owner}/{repo}#{number} has no patchable diffs (binary files only or no changes).")

    combined_diff = "\n\n".join(diff_parts)

    repo_url = f"https://github.com/{owner}/{repo}"
    modules = get_all_modules(repo_url)

    codebase_context = ""
    codebase_aware = False
    extra_system_note = ""

    if modules:
        direct_matches = [m for m in modules if m["path"] in changed_filenames]
        direct_paths = {m["path"] for m in direct_matches}

        keywords = set()
        for filename in changed_filenames:
            keywords.update(
                p.lower() for p in re.split(r"[/\\._\- ]", filename) if len(p) > 2
            )

        keyword_matches = []
        for m in modules:
            if m["path"] in direct_paths:
                continue
            if any(kw in (m.get("summary") or "").lower() for kw in keywords):
                keyword_matches.append(m)
            if len(keyword_matches) >= 3:
                break

        context_modules = direct_matches + keyword_matches
        if context_modules:
            codebase_aware = True
            lines = ["## Related Codebase Context"]
            for m in context_modules:
                lines.append(f"{m['path']}: {m.get('summary', '')}")
            codebase_context = "\n".join(lines)
            extra_system_note = (
                "If codebase context is provided, use it to identify if this PR "
                "could break existing functionality or has dependencies the author "
                "may have missed."
            )

    code_to_review = combined_diff
    if codebase_context:
        code_to_review = f"{combined_diff}\n\n---\n\n{codebase_context}"

    result = await review_code(code_to_review, extra_system_note=extra_system_note)
    result["codebase_aware"] = codebase_aware
    return result
