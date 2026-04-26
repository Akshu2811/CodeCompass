# CodeCompass 
> AI-powered codebase onboarding agent that helps developers understand any GitHub repository instantly.

![Python 3.13](https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python)
![Google ADK](https://img.shields.io/badge/Google%20ADK-1.28.1-4285F4?style=for-the-badge&logo=google)
![Gemini 2.5](https://img.shields.io/badge/LLM-Gemini%202.5-A371F7?style=for-the-badge&logo=google-gemini)
![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688?style=for-the-badge&logo=fastapi)
![Cloud Run](https://img.shields.io/badge/Deployment-Cloud%20Run-4285F4?style=for-the-badge&logo=google-cloud)
![License MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

##  Overview
 onboarding new developers to a complex codebase can take weeks of reading documentation and manually untangling file dependencies. **CodeCompass** solves this by instantly analyzing any GitHub repository and providing a structured, interactive guidance system.

- **Instant Mapping**: Understand module hierarchies and file relationships in seconds.
- **Natural Language Interaction**: Ask complex questions about the architecture and get accurate, context-aware answers.
- **Guided Onboarding**: Generate step-by-step curriculum for new engineers to master the repository.

##  Features
- **Repo Ingestion**: Direct ingestion via GitHub API.
- **AI Module Summarisation**: High-speed file analysis using **Gemini 2.5 Flash**.
- **Semantic Search**: Powered by **text-embedding-004** vectors for sub-second context retrieval.
- **Natural Language Q&A**: Deep reasoning and architecture analysis using **Gemini 2.5 Pro**.
- **Structured Onboarding**: Automatic generation of engineers' learning paths.
- **Professional PDF Export**: Save onboarding guides as typeset, technical documents.
- **Smart Clipboard**: One-click copy for answers and code snippets.
- **Robust Validation**: Enforced GitHub URL patterns for secure ingestion.

## Architecture
```text
User → FastAPI → Orchestrator Agent
          ↓
[Repo Reader, Code Mapper, Q&A Agent, Guide Agent]
          ↓
   SQLite Knowledge Store (Embeddings & Summaries)
```

## Tech Stack
| Component | Technology |
| :--- | :--- |
| **Agent Framework** | Google ADK |
| **LLM (Summarisation)** | Gemini 2.5 Flash |
| **LLM (Reasoning)** | Gemini 2.5 Pro |
| **Embeddings** | text-embedding-004 |
| **Database** | SQLite |
| **API Layer** | FastAPI |
| **Deployment** | Google Cloud Run |
| **IDE** | VS Code / Cursor |

##  Getting Started

### Prerequisites
- Python 3.13+
- Google Cloud Project with Vertex AI enabled.

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Akshu2811/CodeCompass.git
   cd CodeCompass/codecompass
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure Environment (`.env`):
   ```env
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=us-central1
   GOOGLE_GENAI_USE_VERTEXAI=true
   GITHUB_TOKEN=your-github-token
   ```

4. Run locally:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

## API Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/ingest` | Triggers background repository analysis. |
| `GET` | `/status` | Polling endpoint for ingestion progress. |
| `POST` | `/ask` | Semantic Q&A against the code knowledge base. |
| `GET` | `/guide` | Fetches/Generates a persistent onboarding path. |
| `GET` | `/modules` | Lists all discovered modules and their summaries. |

## Demo

**Demo Video:** https://youtu.be/jfWJexESuS4

**Live Demo:** https://codecompass-237057729662.us-central1.run.app

---
**Built for:** Google Gen AI Academy APAC Hackathon 2026  
**Author:** [Akshitha Ganji(Akshu2811)](https://github.com/Akshu2811)
