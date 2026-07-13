"""WebSocket handler for real-time AI chat streaming."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import structlog

from backend.ai.providers import get_provider
from backend.ai.base import ChatMessage
from backend.ai.safety.policy import SafetyPolicy

router = APIRouter()
logger = structlog.get_logger(__name__)
_safety = SafetyPolicy()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    provider = get_provider()

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            history = data.get("history", [])

            safety = _safety.check_input(message)
            if not safety.safe:
                await websocket.send_json({"error": "Message blocked by safety policy"})
                continue

            messages = [
                ChatMessage(role="system", content="You are a helpful enterprise AI assistant."),
            ]
            for turn in history[-6:]:
                messages.append(ChatMessage(role=turn["role"], content=turn["content"]))
            messages.append(ChatMessage(role="user", content=message))

            full_response = []
            async for chunk in provider.stream_chat(messages):
                full_response.append(chunk)
                await websocket.send_json({"chunk": chunk, "done": False})

            await websocket.send_json({"chunk": "", "done": True, "full": "".join(full_response)})

    except WebSocketDisconnect:
        logger.info("websocket_disconnected")
    except Exception as exc:
        logger.exception("websocket_error", error=str(exc))
        await websocket.close(code=1011)
