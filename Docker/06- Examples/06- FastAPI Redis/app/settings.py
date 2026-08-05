import os
REDIS_HOST=os.getenv("REDIS_HOST","redis")
REDIS_PORT=int(os.getenv("REDIS_PORT",6379))
CACHE_TTL=int(os.getenv("CACHE_TTL",60))
