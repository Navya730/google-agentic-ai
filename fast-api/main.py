import ast

from fastapi import FastAPI
from pydantic import BaseModel
from vertexai import agent_engines
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

user_sessions = {}

RESOURCE_ID = "7763809933400735744"


class MessageRequest(BaseModel):
    user_id: str
    message: str

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/chat/send")
def send_message(request: MessageRequest):
    remote_app = agent_engines.get(RESOURCE_ID)
    # Step 1: Check if session exists
    if request.user_id in user_sessions:
        session_id = user_sessions[request.user_id]
    else:
        # Step 2: Create session
        session = remote_app.create_session(user_id=request.user_id)
        session_id = session["id"]
        user_sessions[request.user_id] = session_id

    # Step 3: Send message to the session
    response_events = []
    for event in remote_app.stream_query(
        user_id=request.user_id,
        session_id=session_id,
        message=request.message,
    ):
        response_events.append(str(event))

    parsed = ast.literal_eval(response_events[-1])
    content = parsed["content"]['parts'][0]['text']

    # print(content)

    return {
        "session_id": session_id,
        "responses": content
    }

