from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from db.database import get_all_modules, get_connection
from google.genai import types
import uuid

guide_agent = Agent(
    name="GuideAgent",
    model="gemini-2.5-pro",
    instruction="Given all summaries of a repository, construct an onboarding guide for a new developer."
)

async def get_agent_response(runner, prompt, session_id):
    await runner.session_service.create_session(
        app_name="CodeCompass",
        user_id="user", 
        session_id=session_id
    )
    final_text = ""
    async for event in runner.run_async(
        user_id="user",
        session_id=session_id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )
    ):
        if event.is_final_response():
            final_text = event.content.parts[0].text
            break
    return final_text

async def generate_onboarding_guide(repo_url: str) -> str:
    modules = get_all_modules(repo_url)
    if not modules:
        return "No modules have been indexed for this repository yet."
        
    context = "\n".join([f"{m['path']}: {m['summary']}" for m in modules])
    prompt = f"Create a structured, step-by-step onboarding guide based on these files:\n\n{context}"
    
    runner = Runner(agent=guide_agent, app_name="CodeCompass", session_service=InMemorySessionService())
    
    session_id = uuid.uuid4().hex
    guide_text = await get_agent_response(runner, prompt, session_id)
    
    conn = get_connection()
    conn.execute("INSERT INTO onboarding_paths (repo_url, guide_text) VALUES (?, ?)", (repo_url, guide_text))
    conn.commit()
    conn.close()
    
    return guide_text
