"""
Database models for the playground app.

Uses SQLite. One model: Product.
"""

from django.db import models


class Product(models.Model):
    """
    Product model representing an item in the store.

    This is the only database model in the project.
    All other data (carts, counters, leaderboards, etc.) lives in Redis.
    """

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self) -> str:
        return f"{self.name} (${self.price})"
