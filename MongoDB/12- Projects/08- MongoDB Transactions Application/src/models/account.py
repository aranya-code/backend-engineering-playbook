"""Account domain model used by the MongoDB transactions application."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Account:
    """Represent an account persisted in MongoDB.

    MongoDB stores the account identifier as ``_id`` and the monetary balance
    as a numeric value. The domain model keeps persistence concerns out of
    service-layer business logic while providing a typed representation of
    an account.
    """

    account_id: str
    balance: Decimal

    def __post_init__(self) -> None:
        """Validate invariants required by the account domain model."""
        if not self.account_id.strip():
            raise ValueError("account_id must not be empty")

        if not self.balance.is_finite():
            raise ValueError("balance must be finite")

    @classmethod
    def from_document(cls, document: dict) -> "Account":
        """Create an account from a MongoDB document."""
        account_id = document.get("_id")
        balance = document.get("balance")

        if not isinstance(account_id, str):
            raise ValueError("MongoDB account document requires string '_id'")

        if balance is None:
            raise ValueError("MongoDB account document requires 'balance'")

        return cls(
            account_id=account_id,
            balance=Decimal(str(balance)),
        )

    def to_document(self) -> dict:
        """Convert the domain model into a MongoDB-compatible document."""
        return {
            "_id": self.account_id,
            "balance": float(self.balance),
        }

"""Account domain model used by the MongoDB transactions application."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Account:
    """Represent an account persisted in MongoDB.

    MongoDB stores the account identifier as ``_id`` and the monetary balance
    as a numeric value. The domain model keeps persistence concerns out of
    service-layer business logic while providing a typed representation of
    an account.
    """

    account_id: str
    balance: Decimal

    def __post_init__(self) -> None:
        """Validate invariants required by the account domain model."""
        if not self.account_id.strip():
            raise ValueError("account_id must not be empty")

        if not self.balance.is_finite():
            raise ValueError("balance must be finite")

    @classmethod
    def from_document(cls, document: dict) -> "Account":
        """Create an account from a MongoDB document."""
        account_id = document.get("_id")
        balance = document.get("balance")

        if not isinstance(account_id, str):
            raise ValueError("MongoDB account document requires string '_id'")

        if balance is None:
            raise ValueError("MongoDB account document requires 'balance'")

        return cls(
            account_id=account_id,
            balance=Decimal(str(balance)),
        )

    def to_document(self) -> dict:
        """Convert the domain model into a MongoDB-compatible document."""
        return {
            "_id": self.account_id,
            "balance": float(self.balance),
        }