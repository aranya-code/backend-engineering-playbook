"""Product endpoints with Redis caching."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.schemas import (
    ProductCreate,
    ProductResponse,
    ProductListResponse,
    ProductUpdate,
    MessageResponse
)
from app.services import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Create a new product.
    
    - **name**: Product name
    - **description**: Product description
    - **price**: Product price
    - **stock**: Available stock
    - **category**: Product category
    """
    created_product = await ProductService.create_product(db, product)
    return created_product


@router.get("/", response_model=ProductListResponse)
async def get_products(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum records to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get list of products with caching.
    
    Results are cached in Redis for improved performance.
    Cache is automatically invalidated on product updates.
    """
    products, total = await ProductService.get_products(db, skip, limit, category)
    
    # Convert SQLAlchemy models to Pydantic models
    product_responses = [
        ProductResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            price=p.price,
            stock=p.stock,
            category=p.category,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in products
    ]
    
    return ProductListResponse(
        products=product_responses,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get product by ID with caching.
    
    - Product details are cached in Redis
    - View counter is incremented
    - Leaderboard is updated
    """
    product = await ProductService.get_product(db, product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Handle cached dict or SQLAlchemy model
    if isinstance(product, dict):
        return ProductResponse(**product)
    
    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        category=product.category,
        created_at=product.created_at,
        updated_at=product.updated_at
    )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update product.
    
    Cache is automatically invalidated on update.
    """
    product = await ProductService.update_product(db, product_id, product_update)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product


@router.delete("/{product_id}", response_model=MessageResponse)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete product.
    
    Cache is automatically invalidated on deletion.
    """
    deleted = await ProductService.delete_product(db, product_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return MessageResponse(message=f"Product {product_id} deleted successfully")
