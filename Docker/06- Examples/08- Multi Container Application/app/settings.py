"""
Configuration settings module.
Loads environment variables, providing default values where necessary.
"""
import os
# Load Redis connection details from environment variables
REDIS_HOST=os.getenv('REDIS_HOST','redis')
REDIS_PORT=int(os.getenv('REDIS_PORT',6379))
# Cache Time-To-Live in seconds
CACHE_TTL=int(os.getenv('CACHE_TTL',60))
