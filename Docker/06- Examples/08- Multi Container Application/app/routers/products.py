"""
Products router module for handling product-related API endpoints.
"""
from fastapi import APIRouter
from services.product_service import get_products
router=APIRouter()
@router.get('/products')
def products(): 
    # Fetches products, potentially using a cache
    return get_products()
