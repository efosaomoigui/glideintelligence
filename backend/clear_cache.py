import asyncio
import redis.asyncio as redis

async def main():
    r = redis.from_url('redis://localhost:6379')
    await r.flushdb()
    print('Flushed Redis')
    await r.aclose()

asyncio.run(main())
