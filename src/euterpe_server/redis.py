import redis.asyncio as redis
from typing import Optional

from redis.asyncio.client import Redis
from euterpe_server.config import config

class RedisClient:
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        
    async def connect(self):
        """Initialise connection pool"""
        self.client = redis.from_url(
            config.redis.url.encoded_string(),
            decode_responses=True
        )
        self.client.ping()
        
    async def set_pairing_code(self, code: str, mac_id: str, ex: int = 300):
        """Save pairing code for default 5mins"""
        if self.client:
            await self.client.setex(f"pairing_code:{code}", ex, mac_id)
    
    async def get_mac_id_by_code(self, code: str) -> Optional[str]:
        """Retrieve and delete pairing code"""
        if self.client:
            mac_id = await self.client.get(f"pairing_code:{code}")
            if mac_id:
                await self.client.delete(f"pairing_code:{code}")
            return mac_id
    
    async def save_session(self, token: str, mac_id: str):
        """Save permanent pairing session"""
        if self.client:
            await self.client.set(f"session:{token}", mac_id)
    
    async def get_mac_id_by_session(self, token: str) -> Optional[str]:
        """Validates a JWT/Session token and returns the associated Mac ID."""
        if self.client:
            return await self.client.get(f"session:{token}")

db = RedisClient()