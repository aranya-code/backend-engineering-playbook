"""User API routes for the FastAPI MongoDB REST API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.collection import Collection

from src.database.connection import get_database
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate, UserResponse, UserUpdate
from src.services.user_service import UserService


router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service() -> UserService:
    """Build a user service backed by the configured MongoDB collection."""
    database = get_database()
    collection: Collection = database["users"]
    return UserService(UserRepository(collection))


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Create a new user."""
    try:
        return service.create_user(user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Return a user by ID."""
    user = service.get_user(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.get(
    "",
    response_model=list[UserResponse],
)
def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    active: bool | None = Query(default=None),
    service: UserService = Depends(get_user_service),
) -> list[UserResponse]:
    """Return a paginated list of users."""
    return service.list_users(
        skip=skip,
        limit=limit,
        active=active,
    )


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user(
    user_id: str,
    user: UserUpdate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Update mutable fields of an existing user."""
    try:
        updated_user = service.update_user(user_id, user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if updated_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return updated_user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
) -> None:
    """Delete an existing user."""
    if not service.delete_user(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

"""User API routes for the FastAPI MongoDB REST API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.collection import Collection

from src.database.connection import get_database
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate, UserResponse, UserUpdate
from src.services.user_service import UserService


router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service() -> UserService:
    """Build a user service backed by the configured MongoDB collection."""
    database = get_database()
    collection: Collection = database["users"]
    return UserService(UserRepository(collection))


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Create a new user."""
    try:
        return service.create_user(user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Return a user by ID."""
    user = service.get_user(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.get(
    "",
    response_model=list[UserResponse],
)
def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    active: bool | None = Query(default=None),
    service: UserService = Depends(get_user_service),
) -> list[UserResponse]:
    """Return a paginated list of users."""
    return service.list_users(
        skip=skip,
        limit=limit,
        active=active,
    )


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user(
    user_id: str,
    user: UserUpdate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Update mutable fields of an existing user."""
    try:
        updated_user = service.update_user(user_id, user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if updated_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return updated_user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
) -> None:
    """Delete an existing user."""
    if not service.delete_user(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )