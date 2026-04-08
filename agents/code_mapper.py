import os
import vertexai
vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT", "code-compass-agent"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
)
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from embeddings.vector_search import embed_text
from db.database import save_module
from google.genai import types

mapper_agent = Agent(
    name="CodeMapper",
    model="gemini-2.5-flash",
    instruction="Write a 2-3 sentence summary of the functionality of the provided source code."
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

async def map_code(repo_url: str, path: str, content: str):
    try:
        runner = Runner(agent=mapper_agent, app_name="CodeCompass", session_service=InMemorySessionService())
        prompt = f"File Path: {path}\n\nContent:\n{content}"
        
        session_id = path.replace("/", "_").replace(".", "_")
        summary = await get_agent_response(runner, prompt, session_id)
        
        # embed summary and content
        vector = embed_text(content + "\n" + summary)
        
        save_module(repo_url, path, content, summary, vector)
    except Exception as e:
        print(f"Failed to map code for {path}: {e}")
