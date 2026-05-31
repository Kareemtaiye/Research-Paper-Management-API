import redis.asyncio as redis
import json
import asyncio
from app.core.config import settings
from app.core.logger import logger

REDIS_PUBSUB_URL = (
    settings.prod_redis_pubsub_url
    if settings.is_production
    else (settings.redis_pubsub_url or "redis://redis:6379/3")
)


class PubSubManager:
    def __init__(self):
        self.redis_client = redis.from_url(
            REDIS_PUBSUB_URL, encoding="utf-8", decode_responses=True
        )

    async def publish(self, user_id: str, data: dict):
        # publish event to user's channel
        # logger.info(f"Loop ID: {id(asyncio.get_running_loop())}")
        await self.redis_client.publish(f"user:{user_id}", json.dumps(data))

    # async def subscribe(self, user_id: str):
    #     # subscribe to user's channel
    #     pubsub_obj = self.redis_client.pubsub()
    #     await pubsub_obj.subscribe(f"user:{user_id}")

    #     try:
    #         async for message in pubsub_obj.listen():
    #             if message["type"] == "message":
    #                 yield json.loads((message["data"]))
    #     finally:
    #         await pubsub_obj.unsubscribe(f"user:{user_id}")
    #         await pubsub_obj.close()

    async def subscribe(self, user_id: str):
        pubsub_obj = self.redis_client.pubsub()
        channel = f"user:{user_id}"

        await pubsub_obj.subscribe(channel)

        try:
            while True:
                try:
                    message = await pubsub_obj.get_message(
                        ignore_subscribe_messages=True, timeout=1.0
                    )

                    if message:
                        yield json.loads(message["data"])

                    await asyncio.sleep(0.01)

                except Exception as e:
                    print("PubSub error:", e)
                    await asyncio.sleep(1)
                    continue

        finally:
            await pubsub_obj.unsubscribe(channel)
            await pubsub_obj.close()


# Singleton instance - one manager shared accross the app
pubsub_manager = PubSubManager()
