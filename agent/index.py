from fastapi import FastAPI
from agent.agent import HomeworkAgent
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
agent = HomeworkAgent()

@app.post("/query")
async def query(request: dict):
    question = request.get("question", "")
    conversation_history = request.get("conversation_history", [])
    response = await agent.handle_conversation(question, conversation_history=conversation_history)
    return {"response": response}




if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 9000))
    uvicorn.run(app, host="127.0.0.1", port=port)  # Local only