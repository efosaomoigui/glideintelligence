import json
import functools
import hashlib
from typing import Any, Callable, Optional
from datetime import timedelta
from fastapi.encoders import jsonable_encoder
import redis.asyncio as redis
from app.config import settings

# Initialize Redis client
redis_client: Optional[redis.Redis] = None

def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            settings.REDIS_URL, 
            encoding="utf-8", 
            decode_responses=True
        )
    return redis_client

def cached(ttl: int = 300, prefix: str = "cache"):
    """
    Decorator to cache function results in Redis.
    ttl: Time to live in seconds (default 5 minutes)
    prefix: Key prefix
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Skip cache if Redis is not configured
            if not settings.REDIS_URL:
                return await func(*args, **kwargs)

            # Generate cache key
            key_parts = [prefix, func.__name__]
            if args:
                # Filter out self/db if they are in args
                filtered_args = [str(a) for a in args if not hasattr(a, 'commit')]
                key_parts.extend(filtered_args)
            if kwargs:
                # Filter out db session from kwargs and ensure remaining are JSON serializable
                filtered_kwargs = {k: v for k, v in kwargs.items() if k != 'db'}
                key_parts.append(json.dumps(jsonable_encoder(filtered_kwargs), sort_keys=True))
            
            raw_key = ":".join(key_parts)
            key = hashlib.md5(raw_key.encode()).hexdigest()
            full_key = f"{prefix}:{key}"

            r = get_redis()
            
            # Check cache
            try:
                cached_data = await r.get(full_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                print(f"Cache read error: {e}")

            # Call function
            result = await func(*args, **kwargs)

            # Store in cache
            try:
                if result:
                    # Use jsonable_encoder to ensure Pydantic/SQLAlchemy objects are serializable
                    # We use a try-except here because complex SQLAlchemy models with cycles
                    # can cause recursion depth errors in jsonable_encoder.
                    serialized_data = json.dumps(jsonable_encoder(result))
                    await r.setex(
                        full_key,
                        timedelta(seconds=ttl),
                        serialized_data
                    )
            except Exception as e:
                # If serialization fails, we still return the result, just don't cache it
                print(f"Cache write error (skipping cache): {e}")

            return result
        return wrapper
    return decorator
