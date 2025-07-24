import os
import json
import asyncio
import base64
import warnings
from datetime import datetime
from storetodb import save_conversation
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from dotenv import load_dotenv

from google.genai.types import (
    Part,
    Content,
    Blob,
)

from google.adk.runners import InMemoryRunner, Runner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError

from google_search_agent.agent import root_agent

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

load_dotenv()

APP_NAME = "ADK Streaming example"

import vertexai

conversations = []

client = vertexai.Client(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
)

agent_engine_id = "6630521308419457024"

async def start_agent_session(user_id, is_audio=False):
    """Starts an agent session with working memory integration"""

    print(f"\n🚀 Starting agent session for user: {user_id}")

    # Initialize services
    global session_service


    runner = InMemoryRunner(
        app_name=APP_NAME,
        agent=root_agent,
    )
    print(f"✅ Runner created")

    session = await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
    )

    print(f"✅ Session created: {session.id}")

    # Configure run settings
    modality = "AUDIO" if is_audio else "TEXT"
    run_config = RunConfig(response_modalities=[modality])

    # Create a LiveRequestQueue for this session
    live_request_queue = LiveRequestQueue()

    # Start agent session
    print(f"🚀 Starting live agent session...")
    live_events = runner.run_live(
        session=session,
        live_request_queue=live_request_queue,
        run_config=run_config,
    )

    print(f"✅ Agent session started successfully")
    return live_events, live_request_queue, session


async def agent_to_client_messaging(websocket, live_events):
    """Agent to client communication"""
    try:
        while True:
            async for event in live_events:

                if event.turn_complete or event.interrupted:
                    message = {
                        "turn_complete": event.turn_complete,
                        "interrupted": event.interrupted,
                    }
                    await websocket.send_text(json.dumps(message))
                    print(f"[AGENT TO CLIENT]: {message}")
                    continue

                # Read the Content and its first Part
                part: Part = (
                        event.content and event.content.parts and event.content.parts[0]
                )
                if not part:
                    continue

                # If it's audio, send Base64 encoded audio data
                is_audio = part.inline_data and part.inline_data.mime_type.startswith("audio/pcm")
                if is_audio:
                    audio_data = part.inline_data and part.inline_data.data
                    if audio_data:
                        message = {
                            "mime_type": "audio/pcm",
                            "data": base64.b64encode(audio_data).decode("ascii")
                        }
                        await websocket.send_text(json.dumps(message))
                        conversations.append( {"role": "agent", "content": audio_data} )
                        print(f"[AGENT TO CLIENT]: audio/pcm: {len(audio_data)} bytes.")
                        continue

                # If it's text and a partial text, send it
                if part.text and event.partial:
                    message = {
                        "mime_type": "text/plain",
                        "data": part.text
                    }
                    await websocket.send_text(json.dumps(message))
                    conversations.append({"role": "agent", "content": message["data"]})
                    print(f"[AGENT TO CLIENT]: text/plain: {message}")

    except WebSocketDisconnect:
        print("[AGENT TO CLIENT]: WebSocket disconnected")
    except Exception as e:
        print(f"[AGENT TO CLIENT]: Unexpected error: {e}")


async def client_to_agent_messaging(websocket, live_request_queue):
    """Client to agent communication"""
    try:
        while True:
            # Decode JSON message
            message_json = await websocket.receive_text()
            message = json.loads(message_json)
            mime_type = message["mime_type"]
            data = message["data"]

            # Send the message to the agent
            if mime_type == "text/plain":
                # Send a text message
                content = Content(role="user", parts=[Part.from_text(text=data)])
                live_request_queue.send_content(content=content)
                conversations.append({"role": "user", "content": message["data"]})
                print(f"[CLIENT TO AGENT]: {data}")
            elif mime_type == "audio/pcm":
                # Send an audio data
                conversations.append({"role": "agent", "content": message["data"]})
                decoded_data = base64.b64decode(data)
                live_request_queue.send_realtime(Blob(data=decoded_data, mime_type=mime_type))
            else:
                raise ValueError(f"Mime type not supported: {mime_type}")

    except WebSocketDisconnect:
        # save_conversation(user_id, conversations)
        print("[CLIENT TO AGENT]: WebSocket disconnected")
    except Exception as e:
        print(f"[CLIENT TO AGENT]: Unexpected error: {e}")


# FastAPI web app setup
app = FastAPI()

STATIC_DIR = Path("static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

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
async def root():
    """Serves the index.html"""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, is_audio: str):
    """Enhanced WebSocket endpoint with working memory integration"""

    # Wait for client connection
    await websocket.accept()
    print(f"\n🔌 Client #{user_id} connected, audio mode: {is_audio}")

    # Send periodic pings to keep connection alive in Cloud Run
    async def heartbeat():
        try:
            while True:
                await asyncio.sleep(30)  # Send ping every 30 seconds
                await websocket.send_text("ping")
        except (WebSocketDisconnect, ConnectionClosedError):
            pass
        except Exception as e:
            print(f"Heartbeat error: {e}")

    heartbeat_task = None
    live_request_queue = None
    session_ = None

    try:
        # Start agent session with memory integration
        user_id_str = str(user_id)
        live_events, live_request_queue, session_ = await start_agent_session(user_id_str, is_audio == "true")

        # Start heartbeat task to keep connection alive
        heartbeat_task = asyncio.create_task(heartbeat())

        # Start messaging tasks
        agent_to_client_task = asyncio.create_task(
            agent_to_client_messaging(websocket, live_events)
        )
        client_to_agent_task = asyncio.create_task(
            client_to_agent_messaging(websocket, live_request_queue)
        )

        # Wait until the websocket is disconnected or an error occurs
        tasks = [agent_to_client_task, client_to_agent_task, heartbeat_task]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        # Cancel any pending tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Handle completed tasks and check for exceptions
        for task in done:
            try:
                await task  # This will re-raise any exceptions
            except WebSocketDisconnect:
                print(f"Client #{user_id}: WebSocket disconnected normally")
            except Exception as e:
                print(f"Client #{user_id}: Task completed with error: {e}")

    except WebSocketDisconnect:
        print(f"Client #{user_id}: WebSocket disconnected during setup")
    except Exception as e:
        print(f"Client #{user_id}: Unexpected error in websocket endpoint: {e}")
    finally:
        # Clean up resources
        if heartbeat_task:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

        if live_request_queue:
            live_request_queue.close()

        print(f"🔌 Client #{user_id} disconnected and cleaned up")
        save_conversation(user_id, conversations)


# Health check endpoint for monitoring
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "session_service": "initialized" if session_service else "not_initialized",
        "timestamp": datetime.now().isoformat()
    }