import os
import vertexai
vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT", "code-compass-agent"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
)
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import uuid

orchestrator_agent = Agent(
    name="Orchestrator",
    model="gemini-2.5-flash",
    instruction="Determine if the user wants to 'search', 'guide', or 'ingest'. Output ONLY the one word."
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

async def route_intent(user_input: str) -> str:
    runner = Runner(agent=orchestrator_agent, app_name="CodeCompass", session_service=InMemorySessionService())
    prompt = f"Input: {user_input}"
    
    session_id = uuid.uuid4().hex
    intent_text = await get_agent_response(runner, prompt, session_id)
    
    return intent_text.strip().lower()
