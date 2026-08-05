"""
Cache service module for Redis interactions.
"""
import redis
from settings import REDIS_HOST,REDIS_PORT
# Initialize the Redis client with connection parameters
redis_client=redis.Redis(host=REDIS_HOST,port=REDIS_PORT,decode_responses=True)
