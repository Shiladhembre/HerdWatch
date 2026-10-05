import json
import time
import asyncio
from collections import OrderedDict
from app.config import get_settings


class Cache:
    def __init__(self):
        self.memory = OrderedDict()
        self.redis = None
        self.lock = asyncio.Lock()

    async def connect(self):
        if get_settings().redis_url:
            from redis.asyncio import from_url

            self.redis = from_url(get_settings().redis_url, decode_responses=True, socket_timeout=3)
            await self.redis.ping()

    async def get(self, key):
        if self.redis:
            return json.loads(value) if (value := await self.redis.get(key)) else None
        value = self.memory.get(key)
        if value and value[0] > time.monotonic():
            return value[1]
        self.memory.pop(key, None)
        return None

    async def set(self, key, value, ttl=3600):
        if self.redis:
            await self.redis.setex(key, ttl, json.dumps(value))
            return
        self.memory[key] = (time.monotonic() + ttl, value)
        while len(self.memory) > 512:
            self.memory.popitem(last=False)

    async def close(self):
        if self.redis:
            await self.redis.aclose()


cache = Cache()
