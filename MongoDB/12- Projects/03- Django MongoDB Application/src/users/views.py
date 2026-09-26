"""API views for users backed by MongoDB through PyMongo."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from django.conf import settings
from pymongo import ASCENDING, MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import UserSerializer


_client = MongoClient(
    settings.MONGODB_URI,
    serverSelectionTimeoutMS=settings.MONGODB_SERVER_SELECTION_TIMEOUT_MS,
    connectTimeoutMS=settings.MONGODB_CONNECT_TIMEOUT_MS,
    socketTimeoutMS=settings.MONGODB_SOCKET_TIMEOUT_MS,
    maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
    minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
)

_database = _client[settings.MONGODB_DATABASE]
_users_collection = _database["users"]

_users_collection.create_index(
    [("email", ASCENDING)],
    unique=True,
    name="uq_users_email",
)


@api_view(["GET", "POST"])
def user_list(request) -> Response:
    """List users or create a new user."""
    if request.method == "GET":
        users = list(
            _users_collection.find(
                {},
                {
                    "_id": 1,
                    "name": 1,
                    "email": 1,
                    "is_active": 1,
                    "created_at": 1,
                    "updated_at": 1,
                },
            )
            .sort("created_at", -1)
            .limit(100)
        )

        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    serializer = UserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    now = datetime.now(UTC)
    document = {
        **serializer.validated_data,
        "created_at": now,
        "updated_at": now,
    }

    try:
        result = _users_collection.insert_one(document)
    except DuplicateKeyError:
        return Response(
            {"detail": "A user with this email already exists."},
            status=status.HTTP_409_CONFLICT,
        )
    except PyMongoError:
        return Response(
            {"detail": "Unable to create user."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    document["_id"] = result.inserted_id
    response_serializer = UserSerializer(document)

    return Response(
        response_serializer.data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def user_detail(request, user_id: str) -> Response:
    """Retrieve, update, or delete a user by MongoDB ObjectId."""
    if not ObjectId.is_valid(user_id):
        return Response(
            {"detail": "Invalid user ID."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    object_id = ObjectId(user_id)

    if request.method == "GET":
        try:
            document = _users_collection.find_one({"_id": object_id})
        except PyMongoError:
            return Response(
                {"detail": "Unable to retrieve user."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if document is None:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(UserSerializer(document).data)

    if request.method in {"PUT", "PATCH"}:
        serializer = UserSerializer(
            data=request.data,
            partial=request.method == "PATCH",
        )
        serializer.is_valid(raise_exception=True)

        update_fields: dict[str, Any] = dict(serializer.validated_data)
        update_fields["updated_at"] = datetime.now(UTC)

        try:
            result = _users_collection.find_one_and_update(
                {"_id": object_id},
                {"$set": update_fields},
                return_document=True,
            )
        except DuplicateKeyError:
            return Response(
                {"detail": "A user with this email already exists."},
                status=status.HTTP_409_CONFLICT,
            )
        except PyMongoError:
            return Response(
                {"detail": "Unable to update user."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if result is None:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(UserSerializer(result).data)

    try:
        result = _users_collection.delete_one({"_id": object_id})
    except PyMongoError:
        return Response(
            {"detail": "Unable to delete user."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    if result.deleted_count == 0:
        return Response(
            {"detail": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(status=status.HTTP_204_NO_CONTENT)

"""API views for users backed by MongoDB through PyMongo."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from django.conf import settings
from pymongo import ASCENDING, MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import UserSerializer


_client = MongoClient(
    settings.MONGODB_URI,
    serverSelectionTimeoutMS=settings.MONGODB_SERVER_SELECTION_TIMEOUT_MS,
    connectTimeoutMS=settings.MONGODB_CONNECT_TIMEOUT_MS,
    socketTimeoutMS=settings.MONGODB_SOCKET_TIMEOUT_MS,
    maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
    minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
)

_database = _client[settings.MONGODB_DATABASE]
_users_collection = _database["users"]

_users_collection.create_index(
    [("email", ASCENDING)],
    unique=True,
    name="uq_users_email",
)


@api_view(["GET", "POST"])
def user_list(request) -> Response:
    """List users or create a new user."""
    if request.method == "GET":
        users = list(
            _users_collection.find(
                {},
                {
                    "_id": 1,
                    "name": 1,
                    "email": 1,
                    "is_active": 1,
                    "created_at": 1,
                    "updated_at": 1,
                },
            )
            .sort("created_at", -1)
            .limit(100)
        )

        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    serializer = UserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    now = datetime.now(UTC)
    document = {
        **serializer.validated_data,
        "created_at": now,
        "updated_at": now,
    }

    try:
        result = _users_collection.insert_one(document)
    except DuplicateKeyError:
        return Response(
            {"detail": "A user with this email already exists."},
            status=status.HTTP_409_CONFLICT,
        )
    except PyMongoError:
        return Response(
            {"detail": "Unable to create user."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    document["_id"] = result.inserted_id
    response_serializer = UserSerializer(document)

    return Response(
        response_serializer.data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def user_detail(request, user_id: str) -> Response:
    """Retrieve, update, or delete a user by MongoDB ObjectId."""
    if not ObjectId.is_valid(user_id):
        return Response(
            {"detail": "Invalid user ID."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    object_id = ObjectId(user_id)

    if request.method == "GET":
        try:
            document = _users_collection.find_one({"_id": object_id})
        except PyMongoError:
            return Response(
                {"detail": "Unable to retrieve user."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if document is None:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(UserSerializer(document).data)

    if request.method in {"PUT", "PATCH"}:
        serializer = UserSerializer(
            data=request.data,
            partial=request.method == "PATCH",
        )
        serializer.is_valid(raise_exception=True)

        update_fields: dict[str, Any] = dict(serializer.validated_data)
        update_fields["updated_at"] = datetime.now(UTC)

        try:
            result = _users_collection.find_one_and_update(
                {"_id": object_id},
                {"$set": update_fields},
                return_document=True,
            )
        except DuplicateKeyError:
            return Response(
                {"detail": "A user with this email already exists."},
                status=status.HTTP_409_CONFLICT,
            )
        except PyMongoError:
            return Response(
                {"detail": "Unable to update user."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if result is None:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(UserSerializer(result).data)

    try:
        result = _users_collection.delete_one({"_id": object_id})
    except PyMongoError:
        return Response(
            {"detail": "Unable to delete user."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    if result.deleted_count == 0:
        return Response(
            {"detail": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(status=status.HTTP_204_NO_CONTENT)