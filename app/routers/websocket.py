from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from app.core.security import verify_websocket_token
from app.services.pubsub import pubsub_manager
from app.core.logger import logger

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, token: str = Query()):
    # Validate token before accepting conn
    if not verify_websocket_token(token, user_id):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()  # accept the conn
    try:
        async for message in pubsub_manager.subscribe(user_id):
            await websocket.send_json(message)
    except WebSocketDisconnect:
        pass  # client disconnect cleanly
    except Exception as exc:
        logger.exception(f"Websocket error for user {user_id}: {exc}")
        await websocket.close()
