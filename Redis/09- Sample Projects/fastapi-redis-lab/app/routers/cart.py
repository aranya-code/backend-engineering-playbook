"""Shopping cart endpoints using Redis Hash."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session, get_current_user_id
from app.schemas import CartItemAdd, CartResponse, MessageResponse
from app.services import CartService

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.post("/", response_model=CartResponse, status_code=201)
async def add_to_cart(
    item: CartItemAdd,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Add product to cart.
    
    Cart is stored in Redis Hash for fast access.
    Key format: cart:user:{user_id}
    
    Headers:
    - **X-User-Id**: User identifier (required)
    """
    try:
        cart = await CartService.add_to_cart(
            db,
            user_id,
            item.product_id,
            item.quantity
        )
        return cart
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=CartResponse)
async def get_cart(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get user's cart.
    
    Headers:
    - **X-User-Id**: User identifier (required)
    """
    cart = await CartService.get_cart(user_id, db)
    return cart


@router.delete("/{product_id}", response_model=MessageResponse)
async def remove_from_cart(
    product_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """
    Remove product from cart.
    
    Headers:
    - **X-User-Id**: User identifier (required)
    """
    removed = await CartService.remove_from_cart(user_id, product_id)
    
    if not removed:
        raise HTTPException(status_code=404, detail="Product not in cart")
    
    return MessageResponse(message=f"Product {product_id} removed from cart")


@router.delete("/", response_model=MessageResponse)
async def clear_cart(
    user_id: int = Depends(get_current_user_id)
):
    """
    Clear user's cart.
    
    Headers:
    - **X-User-Id**: User identifier (required)
    """
    cleared = await CartService.clear_cart(user_id)
    
    if not cleared:
        raise HTTPException(status_code=404, detail="Cart is already empty")
    
    return MessageResponse(message="Cart cleared successfully")
