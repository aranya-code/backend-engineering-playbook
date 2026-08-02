"""
DRF serializers for the playground app.
"""

from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for the Product model."""

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "stock",
            "category",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CartItemSerializer(serializers.Serializer):
    """Serializer for adding an item to a shopping cart."""

    user_id = serializers.IntegerField(min_value=1)
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, default=1)


class CartDeleteSerializer(serializers.Serializer):
    """Serializer for clearing a user's cart."""

    user_id = serializers.IntegerField(min_value=1)


class OTPRequestSerializer(serializers.Serializer):
    """Serializer for requesting an OTP."""

    email = serializers.EmailField()


class OTPVerifySerializer(serializers.Serializer):
    """Serializer for verifying an OTP."""

    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)


class PublishSerializer(serializers.Serializer):
    """Serializer for publishing a message to a Redis channel."""

    channel = serializers.CharField(max_length=100)
    message = serializers.CharField(max_length=1000)


class StreamEventSerializer(serializers.Serializer):
    """Serializer for adding an event to a Redis Stream."""

    order_id = serializers.IntegerField(min_value=1)
    event = serializers.CharField(max_length=50)
    data = serializers.DictField(child=serializers.CharField(), required=False, default=dict)
