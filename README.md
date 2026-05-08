# CodeCompass

> AI-powered engineering teammate for codebase onboarding, code review, and architecture Q&A.

![Python](https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python)
![Google ADK](https://img.shields.io/badge/Google%20ADK-1.28.1-4285F4?style=for-the-badge&logo=google)
![Gemini 2.5](https://img.shields.io/badge/LLM-Gemini%202.5-A371F7?style=for-the-badge&logo=google-gemini)
![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688?style=for-the-badge&logo=fastapi)
![Cloud Run](https://img.shields.io/badge/Deployment-Cloud%20Run-4285F4?style=for-the-badge&logo=google-cloud)
![License MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Live:** https://codecompass-237057729662.us-central1.run.app &nbsp;|&nbsp; **GitHub:** https://github.com/Akshu2811/CodeCompass

---

## Capabilities

### 🧭 1. Codebase Onboarding
Paste any GitHub URL. CodeCompass ingests the repo via GitHub API, maps module hierarchies with Gemini 2.5 Flash summaries, stores embeddings (text-embedding-004) in SQLite, and lets you ask natural language questions about the architecture. Also generates a step-by-step onboarding curriculum for new engineers.

### 🔍 2. AI Code Review
Paste raw code or a GitHub PR link. CodeCompass fetches the PR diff via GitHub API, analyses it with Gemini 2.5 Flash, and returns a structured JSON report card:

- **Overall score** (0–100) and **grade** (A–F)
- **Category scores**: Code Quality / Security / Performance / Maintainability / Error Handling
- **Issues ranked**: `CRITICAL` / `WARNING` / `SUGGESTION` with concrete fixes

### 🧠 3. Codebase-Aware Review
When a repo is already ingested, PR reviews cross-reference the diff against the full SQLite knowledge base to catch breaking changes across files. Response includes `codebase_aware: true/false`.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client / UI                          │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼──────────────────────────────────┐
│                     FastAPI (Cloud Run)                      │
└──┬──────────┬──────────┬──────────┬──────────┬──────────────┘
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
Orchestrator  Repo    Code      Q&A        Guide     Review
   Agent     Reader   Mapper    Agent      Agent     Agent
             Agent    Agent
               │        │         │          │         │
               └────────┴─────────┴──────────┘         │
                              │                         │
               ┌──────────────▼──────────────┐         │
               │   SQLite Knowledge Store     │◄────────┘
               │  (Embeddings + Summaries)    │
               └──────────────────────────────┘
                              │
               ┌──────────────▼──────────────┐
               │   Vertex AI / Gemini APIs    │
               │  Flash (speed) · Pro (depth) │
               └──────────────────────────────┘
```

**6 AI agents:** Orchestrator · Repo Reader · Code Mapper · Q&A Agent · Guide Agent · Review Agent

---

## Tech Stack

| Component | Technology |
| :--- | :--- |
| Agent Framework | Google ADK |
| LLM — Summarisation & Review | Gemini 2.5 Flash |
| LLM — Deep Reasoning / Q&A | Gemini 2.5 Pro |
| Embeddings | text-embedding-004 |
| Knowledge Store | SQLite |
| API Layer | FastAPI |
| Deployment | Google Cloud Run |
| AI Platform | Vertex AI |

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/ingest` | Ingest a GitHub repo (triggers background analysis) |
| `GET` | `/status` | Poll ingestion progress |
| `POST` | `/ask` | Natural language Q&A against the knowledge base |
| `GET` | `/guide` | Generate step-by-step onboarding curriculum |
| `GET` | `/modules` | List all modules with AI-generated summaries |
| `POST` | `/review` | Review pasted code and return a JSON report card |
| `POST` | `/review-pr` | Review a GitHub PR URL (codebase-aware if repo ingested) |

---

## Getting Started

### Prerequisites
- Python 3.13+
- Google Cloud project with Vertex AI enabled
- GitHub personal access token

### Installation

```bash
git clone https://github.com/Akshu2811/CodeCompass.git
cd CodeCompass/codecompass
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in `codecompass/`:

```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=true
GITHUB_TOKEN=your-github-token
```

### Run Locally

```bash
uvicorn main:app --reload --port 8000
```

---

---

## Live Demo

**Live:** https://codecompass-237057729662.us-central1.run.app

---

**Author:** [Akshitha Ganji](https://github.com/Akshu2811) &nbsp;|&nbsp; **Built for:** upGrad AI Verse Hackathon 2026
