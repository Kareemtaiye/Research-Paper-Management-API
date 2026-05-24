import redis.asyncio as redis
import json
from app.core.config import settings

REDIS_PUBSUB_URL = settings.redis_pubsub_url or "redis://redis:6379/3"


class PubSubManager:
    def __init__(self):
        self.redis_client = redis.from_url(
            REDIS_PUBSUB_URL, encoding="utf-8", decode_responses=True
        )

    async def publish(self, user_id: str, data: dict):
        # publish event to user's channel
        await self.redis_client.publish(f"user:{user_id}", json.dumps(data))

    async def subscribe(self, user_id: str):
        # subscribe to user's channel
        pubsub_obj = self.redis_client.pubsub()
        await pubsub_obj.subscribe(f"user:{user_id}")

        try:
            async for message in pubsub_obj.listen():
                if message["type"] == "message":
                    yield json.loads((message["data"]))
        finally:
            await pubsub_obj.unsubscribe(f"user:{user_id}")
            await pubsub_obj.close()


# Singleton instance - one manager shared accross the app
pubsub_manager = PubSubManager()
