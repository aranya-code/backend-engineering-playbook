"""
Product service module demonstrating the cache-aside pattern.
"""
import json,time
from services.cache_service import redis_client
from settings import CACHE_TTL

PRODUCTS=[{"id":1,"name":"Keyboard","price":99},{"id":2,"name":"Mouse","price":49}]

def get_products():
 # Cache-aside pattern: check cache first
 c=redis_client.get("products")
 if c: 
     # Cache hit: return the stored data
     return json.loads(c)
 # Cache miss: compute/fetch the data (simulated with sleep)
 time.sleep(5)
 # Store the computed data in the cache for future requests
 redis_client.setex("products",CACHE_TTL,json.dumps(PRODUCTS))
 return PRODUCTS
