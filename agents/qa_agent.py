from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from embeddings.vector_search import search_related_modules
from db.database import get_connection
from google.genai import types
import time
import uuid

qa_agent = Agent(
    name="QAAgent",
    model="gemini-2.5-pro",
    instruction="You answer questions about the codebase based only on the retrieved context."
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

async def answer_question(repo_url: str, question: str) -> str:
    try:
        results = search_related_modules(repo_url, question, top_k=3)
        context = "\n".join([f"--- PATH: {r[1]} ---\n{r[2]}" for r in results])
        
        if not context:
            return "I could not find relevant code to answer the question."
            
        prompt = f"User Question: {question}\n\nContext:\n{context}\n\nPlease formulate an answer."
        runner = Runner(agent=qa_agent, app_name="CodeCompass", session_service=InMemorySessionService())
        
        session_id = uuid.uuid4().hex
        answer = await get_agent_response(runner, prompt, session_id)
        
        # record answer locally
        conn = get_connection()
        conn.execute("INSERT INTO qa_history (repo_url, question, answer) VALUES (?, ?, ?)", (repo_url, question, answer))
        conn.commit()
        conn.close()
        
        return answer
    except Exception as e:
        print(f"Failed to answer question: {e}")
        return "An error occurred answering your question."
