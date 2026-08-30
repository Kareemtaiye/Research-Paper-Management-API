from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from jwt import ExpiredSignatureError, InvalidTokenError
from app.core.security import verify_websocket_token
from app.services.pubsub import pubsub_manager
from app.core.logger import logger

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, token: str = Query()):
    # Accept first — completes the WebSocket handshake
    await websocket.accept()

    # Validate token before accepting conn
    try:
        valid = verify_websocket_token(token, user_id)
    except ExpiredSignatureError:
        await websocket.close(code=4001, reason="Token expired")
        return
    except InvalidTokenError:
        await websocket.close(code=4002, reason="Invalid token")
        return
    except Exception as e:
        logger.error(f"WS auth failed: {type(e).__name__}: {e}")
        await websocket.close(code=4003, reason="Unauthorized")
        return

    if not valid:
        await websocket.close(code=4003, reason="Unauthorized")
        return
    # if not verify_websocket_token(token, user_id):
    #     await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    #     return

    try:
        async for message in pubsub_manager.subscribe(user_id):
            await websocket.send_json(message)
    except WebSocketDisconnect:
        pass  # client disconnect cleanly
    except Exception as exc:
        logger.exception(f"Websocket error for user {user_id}: {exc}")
        await websocket.close()
