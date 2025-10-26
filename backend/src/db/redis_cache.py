# Redis (caching layer) for JWT blocklist (to invalidate tokens) by JWT ID (JTI)
import redis.asyncio as redis
from src.config import Config

JTI_EXPIRY = 3600

token_blocklist = redis.StrictRedis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    db=0
)

# token_blocklist = redis.from_url(Config.REDIS_URL)

async def add_jti_to_blocklist(jti: str) -> None:
    await token_blocklist.set(name=jti, value="", ex=JTI_EXPIRY)

async def token_in_blocklist(jti: str) -> bool:
    result = await token_blocklist.get(jti)
    return False if await token_blocklist.get(jti) is None else True