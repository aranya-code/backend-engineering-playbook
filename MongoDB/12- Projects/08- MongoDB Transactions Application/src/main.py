"""MongoDB transactions application entry point."""

from __future__ import annotations

import os
from typing import Any

from pymongo import MongoClient
from pymongo.errors import PyMongoError


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "mongodb_transactions",
)


def get_client() -> MongoClient:
    """Create a MongoDB client using application configuration."""
    return MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5_000,
        connectTimeoutMS=5_000,
        socketTimeoutMS=30_000,
        retryWrites=True,
    )


def transfer_balance(
    client: MongoClient,
    *,
    from_account: str,
    to_account: str,
    amount: float,
) -> None:
    """Transfer funds between two accounts atomically.

    The operation uses a MongoDB session and multi-document transaction so
    either both account updates commit or neither update is persisted.
    """
    if amount <= 0:
        raise ValueError("amount must be greater than zero")

    database = client[MONGODB_DATABASE]
    accounts = database["accounts"]

    with client.start_session() as session:
        with session.start_transaction():
            source = accounts.find_one(
                {"_id": from_account},
                session=session,
            )

            if source is None:
                raise ValueError(f"source account not found: {from_account}")

            if source.get("balance", 0) < amount:
                raise ValueError("insufficient account balance")

            destination = accounts.find_one(
                {"_id": to_account},
                session=session,
            )

            if destination is None:
                raise ValueError(
                    f"destination account not found: {to_account}"
                )

            source_result = accounts.update_one(
                {"_id": from_account},
                {"$inc": {"balance": -amount}},
                session=session,
            )

            destination_result = accounts.update_one(
                {"_id": to_account},
                {"$inc": {"balance": amount}},
                session=session,
            )

            if (
                source_result.modified_count != 1
                or destination_result.modified_count != 1
            ):
                raise RuntimeError(
                    "transaction did not update both accounts"
                )


def main() -> int:
    """Run the MongoDB transaction example."""
    client = get_client()

    try:
        client.admin.command("ping")

        transfer_balance(
            client,
            from_account="account-001",
            to_account="account-002",
            amount=100.00,
        )

        print("Transaction committed successfully.")
        return 0
    except (PyMongoError, ValueError, RuntimeError) as exc:
        print(f"Transaction failed: {exc}")
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())

"""MongoDB transactions application entry point."""

from __future__ import annotations

import os
from typing import Any

from pymongo import MongoClient
from pymongo.errors import PyMongoError


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "mongodb_transactions",
)


def get_client() -> MongoClient:
    """Create a MongoDB client using application configuration."""
    return MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5_000,
        connectTimeoutMS=5_000,
        socketTimeoutMS=30_000,
        retryWrites=True,
    )


def transfer_balance(
    client: MongoClient,
    *,
    from_account: str,
    to_account: str,
    amount: float,
) -> None:
    """Transfer funds between two accounts atomically.

    The operation uses a MongoDB session and multi-document transaction so
    either both account updates commit or neither update is persisted.
    """
    if amount <= 0:
        raise ValueError("amount must be greater than zero")

    database = client[MONGODB_DATABASE]
    accounts = database["accounts"]

    with client.start_session() as session:
        with session.start_transaction():
            source = accounts.find_one(
                {"_id": from_account},
                session=session,
            )

            if source is None:
                raise ValueError(f"source account not found: {from_account}")

            if source.get("balance", 0) < amount:
                raise ValueError("insufficient account balance")

            destination = accounts.find_one(
                {"_id": to_account},
                session=session,
            )

            if destination is None:
                raise ValueError(
                    f"destination account not found: {to_account}"
                )

            source_result = accounts.update_one(
                {"_id": from_account},
                {"$inc": {"balance": -amount}},
                session=session,
            )

            destination_result = accounts.update_one(
                {"_id": to_account},
                {"$inc": {"balance": amount}},
                session=session,
            )

            if (
                source_result.modified_count != 1
                or destination_result.modified_count != 1
            ):
                raise RuntimeError(
                    "transaction did not update both accounts"
                )


def main() -> int:
    """Run the MongoDB transaction example."""
    client = get_client()

    try:
        client.admin.command("ping")

        transfer_balance(
            client,
            from_account="account-001",
            to_account="account-002",
            amount=100.00,
        )

        print("Transaction committed successfully.")
        return 0
    except (PyMongoError, ValueError, RuntimeError) as exc:
        print(f"Transaction failed: {exc}")
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())