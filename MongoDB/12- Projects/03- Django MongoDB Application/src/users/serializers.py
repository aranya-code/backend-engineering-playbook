"""Serialization helpers for the users application.

The application uses MongoDB through PyMongo rather than Django's ORM.
Serializers therefore operate on plain dictionaries and MongoDB documents.
"""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from rest_framework import serializers


class ObjectIdField(serializers.Field):
    """Serialize and validate MongoDB ObjectId values."""

    def to_representation(self, value: ObjectId | str) -> str:
        """Return an ObjectId as its canonical hexadecimal string."""
        return str(value)

    def to_internal_value(self, data: Any) -> ObjectId:
        """Convert a valid hexadecimal ObjectId string to ObjectId."""
        if isinstance(data, ObjectId):
            return data

        if not isinstance(data, str) or not ObjectId.is_valid(data):
            raise serializers.ValidationError("Invalid MongoDB ObjectId.")

        return ObjectId(data)


class UserSerializer(serializers.Serializer):
    """Validate and serialize MongoDB user documents."""

    id = ObjectIdField(read_only=True)
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=254)
    is_active = serializers.BooleanField(default=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def to_representation(self, instance: dict[str, Any]) -> dict[str, Any]:
        """Map MongoDB's ``_id`` field to the API's ``id`` field."""
        document = dict(instance)

        if "_id" in document and "id" not in document:
            document["id"] = document.pop("_id")

        return super().to_representation(document)

"""Serialization helpers for the users application.

The application uses MongoDB through PyMongo rather than Django's ORM.
Serializers therefore operate on plain dictionaries and MongoDB documents.
"""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from rest_framework import serializers


class ObjectIdField(serializers.Field):
    """Serialize and validate MongoDB ObjectId values."""

    def to_representation(self, value: ObjectId | str) -> str:
        """Return an ObjectId as its canonical hexadecimal string."""
        return str(value)

    def to_internal_value(self, data: Any) -> ObjectId:
        """Convert a valid hexadecimal ObjectId string to ObjectId."""
        if isinstance(data, ObjectId):
            return data

        if not isinstance(data, str) or not ObjectId.is_valid(data):
            raise serializers.ValidationError("Invalid MongoDB ObjectId.")

        return ObjectId(data)


class UserSerializer(serializers.Serializer):
    """Validate and serialize MongoDB user documents."""

    id = ObjectIdField(read_only=True)
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=254)
    is_active = serializers.BooleanField(default=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def to_representation(self, instance: dict[str, Any]) -> dict[str, Any]:
        """Map MongoDB's ``_id`` field to the API's ``id`` field."""
        document = dict(instance)

        if "_id" in document and "id" not in document:
            document["id"] = document.pop("_id")

        return super().to_representation(document)