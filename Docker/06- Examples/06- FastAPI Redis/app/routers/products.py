import json
from fastapi import APIRouter
from cache import redis_client
from services.product_service import load_products
from settings import CACHE_TTL

router=APIRouter()

@router.get("/products")
def products():
    cached=redis_client.get("products")
    if cached:
        return {"cached":True,"source":"redis","products":json.loads(cached)}
    data=load_products()
    redis_client.setex("products",CACHE_TTL,json.dumps(data))
    return {"cached":False,"source":"service","products":data}

@router.delete("/cache/products")
def clear_cache():
    redis_client.delete("products")
    return {"message":"Cache cleared"}
