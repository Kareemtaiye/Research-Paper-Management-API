import redis.asyncio as redis
import json
from app.core.config import settings

PAPER_STREAM = "user_events"
REDIS_PUBSUB_URL = settings.redis_pubsub_url or "redis://redis:6379/3"


class StreamManager:
    def __init__(self):
        self.redis = redis.from_url(REDIS_PUBSUB_URL, decode_responses=True)

    async def publish(self, user_id: str, data: dict):
        """Write event to Redis Stream"""
        await self.redis.xadd(
            f"{PAPER_STREAM}:{user_id}", {"payload": json.dumps(data)}
        )

    async def subscribe(self, user_id: str):
        """
        Stream consumer (replaces pubsub.listen())
        """
        stream_key = f"{PAPER_STREAM}:{user_id}"
        last_id = "$"

        while True:
            events = await self.redis.xread({stream_key: last_id}, block=5000, count=10)

            if not events:
                continue

            _, messages = events[0]

            for message_id, data in messages:
                last_id = message_id

                yield json.loads(data["payload"])


stream_manager = StreamManager()
