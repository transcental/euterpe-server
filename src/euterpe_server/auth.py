import jwt
import time

from euterpe_server.config import config

def create_access_token(user_id: str):
    payload = {
        "user_id": user_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + (60 * 60 * 24 * 365)  # Token valid for 1 year
    }
    return jwt.encode(payload, config.secret_key, algorithm="HS256")

async def get_user_from_token(token: str | None):
    if not token: return None
    try:
        decoded = jwt.decode(token, config.secret_key, algorithms=["HS256"])
        return decoded.get("user_id")
    except jwt.PyJWTError:
        return None
