"""Service layer for product business operations."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from repositories.product_repository import (
    adjust_stock,
    create_product,
    delete_product,
    get_product_by_id,
    get_product_by_sku,
    list_products,
    search_products,
    update_product,
)


def create_product_service(
    *,
    name: str,
    sku: str,
    price: Decimal | str | float,
    category: str,
    stock_quantity: int = 0,
    description: str | None = None,
    is_active: bool = True,
) -> dict[str, Any]:
    """Create a product after applying service-level business rules."""
    normalized_name = name.strip()
    normalized_sku = sku.strip().upper()
    normalized_category = category.strip()

    if not normalized_name:
        raise ValueError("Product name cannot be empty.")

    if not normalized_sku:
        raise ValueError("Product SKU cannot be empty.")

    if not normalized_category:
        raise ValueError("Product category cannot be empty.")

    if stock_quantity < 0:
        raise ValueError("Stock quantity cannot be negative.")

    normalized_price = Decimal(str(price))

    if normalized_price < 0:
        raise ValueError("Product price cannot be negative.")

    if get_product_by_sku(normalized_sku) is not None:
        raise ValueError("A product with this SKU already exists.")

    try:
        return create_product(
            name=normalized_name,
            sku=normalized_sku,
            price=normalized_price,
            category=normalized_category,
            stock_quantity=stock_quantity,
            description=description,
            is_active=is_active,
        )
    except DuplicateKeyError as exc:
        # Protect against a race between the existence check and insert.
        raise ValueError(
            "A product with this SKU already exists.",
        ) from exc


def get_product_service(
    product_id: ObjectId,
) -> dict[str, Any] | None:
    """Return a product by identifier."""
    if not isinstance(product_id, ObjectId):
        raise ValueError("product_id must be a valid ObjectId.")

    return get_product_by_id(product_id)


def get_product_by_sku_service(
    sku: str,
) -> dict[str, Any] | None:
    """Return a product by normalized SKU."""
    normalized_sku = sku.strip().upper()

    if not normalized_sku:
        raise ValueError("SKU cannot be empty.")

    return get_product_by_sku(normalized_sku)


def list_products_service(
    *,
    skip: int = 0,
    limit: int = 50,
    category: str | None = None,
    is_active: bool | None = None,
) -> list[dict[str, Any]]:
    """Return products using bounded pagination."""
    if skip < 0:
        raise ValueError("skip cannot be negative.")

    if limit <= 0 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")

    return list_products(
        skip=skip,
        limit=limit,
        category=category,
        is_active=is_active,
    )


def search_products_service(
    search_term: str,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Search active products using the product repository."""
    if not search_term.strip():
        raise ValueError("search_term cannot be empty.")

    if limit <= 0 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")

    return search_products(
        search_term,
        limit=limit,
    )


def update_product_service(
    product_id: ObjectId,
    *,
    name: str | None = None,
    price: Decimal | str | float | None = None,
    category: str | None = None,
    stock_quantity: int | None = None,
    description: str | None = None,
    is_active: bool | None = None,
) -> dict[str, Any] | None:
    """Update a product after validating business rules."""
    if not isinstance(product_id, ObjectId):
        raise ValueError("product_id must be a valid ObjectId.")

    if name is not None and not name.strip():
        raise ValueError("Product name cannot be empty.")

    if category is not None and not category.strip():
        raise ValueError("Product category cannot be empty.")

    if price is not None:
        normalized_price = Decimal(str(price))

        if normalized_price < 0:
            raise ValueError("Product price cannot be negative.")

    if stock_quantity is not None and stock_quantity < 0:
        raise ValueError("Stock quantity cannot be negative.")

    return update_product(
        product_id,
        name=name,
        price=price,
        category=category,
        stock_quantity=stock_quantity,
        description=description,
        is_active=is_active,
    )


def adjust_product_stock_service(
    product_id: ObjectId,
    quantity_delta: int,
) -> dict[str, Any] | None:
    """Atomically adjust product inventory."""
    if not isinstance(product_id, ObjectId):
        raise ValueError("product_id must be a valid ObjectId.")

    if quantity_delta == 0:
        raise ValueError("quantity_delta cannot be zero.")

    return adjust_stock(
        product_id,
        quantity_delta,
    )


def delete_product_service(product_id: ObjectId) -> bool:
    """Delete a product by identifier."""
    if not isinstance(product_id, ObjectId):
        raise ValueError("product_id must be a valid ObjectId.")

    return delete_product(product_id)

"""Service layer for product business operations."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from repositories.product_repository import (
    adjust_stock,
    create_product,
    delete_product,
    get_product_by_id,
    get_product_by_sku,
    list_products,
    search_products,
    update_product,
)


def create_product_service(
    *,
    name: str,
    sku: str,
    price: Decimal | str | float,
    category: str,
    stock_quantity: int = 0,
    description: str | None = None,
    is_active: bool = True,
) -> dict[str, Any]:
    """Create a product after applying service-level business rules."""
    normalized_name = name.strip()
    normalized_sku = sku.strip().upper()
    normalized_category = category.strip()

    if not normalized_name:
        raise ValueError("Product name cannot be empty.")

    if not normalized_sku:
        raise ValueError("Product SKU cannot be empty.")

    if not normalized_category:
        raise ValueError("Product category cannot be empty.")

    if stock_quantity < 0:
        raise ValueError("Stock quantity cannot be negative.")

    normalized_price = Decimal(str(price))

    if normalized_price < 0:
        raise ValueError("Product price cannot be negative.")

    if get_product_by_sku(normalized_sku) is not None:
        raise ValueError("A product with this SKU already exists.")

    try:
        return create_product(
            name=normalized_name,
            sku=normalized_sku,
            price=normalized_price,
            category=normalized_category,
            stock_quantity=stock_quantity,
            description=description,
            is_active=is_active,
        )
    except DuplicateKeyError as exc:
        # Protect against a race between the existence check and insert.
        raise ValueError(
            "A product with this SKU already exists.",
        ) from exc


def get_product_service(
    product_id: ObjectId,
) -> dict[str, Any] | None:
    """Return a product by identifier."""
    if not isinstance(product_id, ObjectId):
        raise ValueError("product_id must be a valid ObjectId.")

    return get_product_by_id(product_id)


def get_product_by_sku_service(
    sku: str,
) -> dict[str, Any] | None:
    """Return a product by normalized SKU."""
    normalized_sku = sku.strip().upper()

    if not normalized_sku:
        raise ValueError("SKU cannot be empty.")

    return get_product_by_sku(normalized_sku)


def list_products_service(
    *,
    skip: int = 0,
    limit: int = 50,
    category: str | None = None,
    is_active: bool | None = None,
) -> list[dict[str, Any]]:
    """Return products using bounded pagination."""
    if skip < 0:
        raise ValueError("skip cannot be negative.")

    if limit <= 0 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")

    return list_products(
        skip=skip,
        limit=limit,
        category=category,
        is_active=is_active,
    )


def search_products_service(
    search_term: str,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Search active products using the product repository."""
    if not search_term.strip():
        raise ValueError("search_term cannot be empty.")

    if limit <= 0 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")

    return search_products(
        search_term,
        limit=limit,
    )


def update_product_service(
    product_id: ObjectId,
    *,
    name: str | None = None,
    price: Decimal | str | float | None = None,
    category: str | None = None,
    stock_quantity: int | None = None,
    description: str | None = None,
    is_active: bool | None = None,
) -> dict[str, Any] | None:
    """Update a product after validating business rules."""
    if not isinstance(product_id, ObjectId):
        raise ValueError("product_id must be a valid ObjectId.")

    if name is not None and not name.strip():
        raise ValueError("Product name cannot be empty.")

    if category is not None and not category.strip():
        raise ValueError("Product category cannot be empty.")

    if price is not None:
        normalized_price = Decimal(str(price))

        if normalized_price < 0:
            raise ValueError("Product price cannot be negative.")

    if stock_quantity is not None and stock_quantity < 0:
        raise ValueError("Stock quantity cannot be negative.")

    return update_product(
        product_id,
        name=name,
        price=price,
        category=category,
        stock_quantity=stock_quantity,
        description=description,
        is_active=is_active,
    )


def adjust_product_stock_service(
    product_id: ObjectId,
    quantity_delta: int,
) -> dict[str, Any] | None:
    """Atomically adjust product inventory."""
    if not isinstance(product_id, ObjectId):
        raise ValueError("product_id must be a valid ObjectId.")

    if quantity_delta == 0:
        raise ValueError("quantity_delta cannot be zero.")

    return adjust_stock(
        product_id,
        quantity_delta,
    )


def delete_product_service(product_id: ObjectId) -> bool:
    """Delete a product by identifier."""
    if not isinstance(product_id, ObjectId):
        raise ValueError("product_id must be a valid ObjectId.")

    return delete_product(product_id)