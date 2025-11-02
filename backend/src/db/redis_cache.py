# Redis (caching layer) for JWT blocklist (to invalidate tokens) by JWT ID (JTI)
import redis.asyncio as redis
from src.config import Config

JTI_EXPIRY = 3600

redis_client = redis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    db=0
)

# token_blocklist = redis.from_url(Config.REDIS_URL)

async def add_jti_to_blocklist(jti: str) -> None:
    await redis_client.set(name=f"blocklist:{jti}", value="", ex=JTI_EXPIRY)

async def token_in_blocklist(jti: str) -> bool:
    return True if await redis_client.exists(f"blocklist:{jti}") else False

async def cache_research_response(result_id: str, research_result_str: str):
    await redis_client.set(f"research:{result_id}", research_result_str)

async def get_cached_research_response(result_id: str):
    res = await redis_client.get(f"research:{result_id}")
    return None if not res else res