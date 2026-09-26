"""Business service for atomic MongoDB account transfers."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pymongo import MongoClient
from pymongo.errors import PyMongoError
from pymongo.read_concern import ReadConcern
from pymongo.read_preferences import Primary
from pymongo.write_concern import WriteConcern


class TransferError(Exception):
    """Base exception for account transfer failures."""


class AccountNotFoundError(TransferError):
    """Raised when an account required for a transfer does not exist."""


class InsufficientFundsError(TransferError):
    """Raised when the source account lacks sufficient funds."""


class TransferService:
    """Coordinate atomic account transfers using MongoDB transactions.

    The service owns the transaction boundary while database-specific access
    remains limited to the operations required by the transfer use case.
    """

    def __init__(
        self,
        client: MongoClient,
        *,
        database_name: str,
        collection_name: str = "accounts",
    ) -> None:
        """Initialize the transfer service.

        Args:
            client: Shared application-level MongoDB client.
            database_name: MongoDB database containing account documents.
            collection_name: Collection containing account documents.
        """
        if not database_name.strip():
            raise ValueError("database_name must not be empty")

        if not collection_name.strip():
            raise ValueError("collection_name must not be empty")

        self._database = client[database_name]
        self._accounts = self._database.get_collection(
            collection_name,
            read_preference=Primary(),
            read_concern=ReadConcern("local"),
            write_concern=WriteConcern(w="majority"),
        )
        self._client = client

    def transfer(
        self,
        *,
        from_account: str,
        to_account: str,
        amount: Decimal,
    ) -> None:
        """Transfer funds between two accounts atomically.

        The transaction updates both accounts or neither account. The source
        balance is checked as part of the conditional update, preventing the
        service from relying solely on a previously read balance.

        Args:
            from_account: Identifier of the source account.
            to_account: Identifier of the destination account.
            amount: Positive transfer amount.

        Raises:
            ValueError: If account identifiers or amount are invalid.
            AccountNotFoundError: If either account does not exist.
            InsufficientFundsError: If the source lacks sufficient funds.
            TransferError: If MongoDB rejects the transaction.
        """
        self._validate_transfer(
            from_account=from_account,
            to_account=to_account,
            amount=amount,
        )

        with self._client.start_session() as session:

            def transaction_callback(
                transaction_session: Any,
            ) -> None:
                self._execute_transfer(
                    transaction_session,
                    from_account=from_account,
                    to_account=to_account,
                    amount=amount,
                )

            try:
                session.with_transaction(
                    transaction_callback,
                    read_concern=ReadConcern("local"),
                    write_concern=WriteConcern(w="majority"),
                    read_preference=Primary(),
                )
            except TransferError:
                raise
            except PyMongoError as exc:
                raise TransferError(
                    "MongoDB transaction failed"
                ) from exc

    def _execute_transfer(
        self,
        session: Any,
        *,
        from_account: str,
        to_account: str,
        amount: Decimal,
    ) -> None:
        """Execute the transfer inside an active MongoDB transaction."""
        source = self._accounts.find_one(
            {"_id": from_account},
            session=session,
            projection={"_id": 1},
        )

        if source is None:
            raise AccountNotFoundError(
                f"source account not found: {from_account}"
            )

        destination = self._accounts.find_one(
            {"_id": to_account},
            session=session,
            projection={"_id": 1},
        )

        if destination is None:
            raise AccountNotFoundError(
                f"destination account not found: {to_account}"
            )

        amount_value = float(amount)

        source_result = self._accounts.update_one(
            {
                "_id": from_account,
                "balance": {"$gte": amount_value},
            },
            {
                "$inc": {"balance": -amount_value},
            },
            session=session,
        )

        if source_result.modified_count != 1:
            raise InsufficientFundsError(
                f"insufficient funds in account: {from_account}"
            )

        destination_result = self._accounts.update_one(
            {"_id": to_account},
            {
                "$inc": {"balance": amount_value},
            },
            session=session,
        )

        if destination_result.modified_count != 1:
            raise AccountNotFoundError(
                f"destination account not found: {to_account}"
            )

    @staticmethod
    def _validate_transfer(
        *,
        from_account: str,
        to_account: str,
        amount: Decimal,
    ) -> None:
        """Validate transfer input before opening a database transaction."""
        if not from_account.strip():
            raise ValueError("from_account must not be empty")

        if not to_account.strip():
            raise ValueError("to_account must not be empty")

        if from_account == to_account:
            raise ValueError(
                "source and destination accounts must be different"
            )

        if amount <= Decimal("0"):
            raise ValueError("amount must be greater than zero")

        if not amount.is_finite():
            raise ValueError("amount must be finite")

"""Business service for atomic MongoDB account transfers."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pymongo import MongoClient
from pymongo.errors import PyMongoError
from pymongo.read_concern import ReadConcern
from pymongo.read_preferences import Primary
from pymongo.write_concern import WriteConcern


class TransferError(Exception):
    """Base exception for account transfer failures."""


class AccountNotFoundError(TransferError):
    """Raised when an account required for a transfer does not exist."""


class InsufficientFundsError(TransferError):
    """Raised when the source account lacks sufficient funds."""


class TransferService:
    """Coordinate atomic account transfers using MongoDB transactions.

    The service owns the transaction boundary while database-specific access
    remains limited to the operations required by the transfer use case.
    """

    def __init__(
        self,
        client: MongoClient,
        *,
        database_name: str,
        collection_name: str = "accounts",
    ) -> None:
        """Initialize the transfer service.

        Args:
            client: Shared application-level MongoDB client.
            database_name: MongoDB database containing account documents.
            collection_name: Collection containing account documents.
        """
        if not database_name.strip():
            raise ValueError("database_name must not be empty")

        if not collection_name.strip():
            raise ValueError("collection_name must not be empty")

        self._database = client[database_name]
        self._accounts = self._database.get_collection(
            collection_name,
            read_preference=Primary(),
            read_concern=ReadConcern("local"),
            write_concern=WriteConcern(w="majority"),
        )
        self._client = client

    def transfer(
        self,
        *,
        from_account: str,
        to_account: str,
        amount: Decimal,
    ) -> None:
        """Transfer funds between two accounts atomically.

        The transaction updates both accounts or neither account. The source
        balance is checked as part of the conditional update, preventing the
        service from relying solely on a previously read balance.

        Args:
            from_account: Identifier of the source account.
            to_account: Identifier of the destination account.
            amount: Positive transfer amount.

        Raises:
            ValueError: If account identifiers or amount are invalid.
            AccountNotFoundError: If either account does not exist.
            InsufficientFundsError: If the source lacks sufficient funds.
            TransferError: If MongoDB rejects the transaction.
        """
        self._validate_transfer(
            from_account=from_account,
            to_account=to_account,
            amount=amount,
        )

        with self._client.start_session() as session:

            def transaction_callback(
                transaction_session: Any,
            ) -> None:
                self._execute_transfer(
                    transaction_session,
                    from_account=from_account,
                    to_account=to_account,
                    amount=amount,
                )

            try:
                session.with_transaction(
                    transaction_callback,
                    read_concern=ReadConcern("local"),
                    write_concern=WriteConcern(w="majority"),
                    read_preference=Primary(),
                )
            except TransferError:
                raise
            except PyMongoError as exc:
                raise TransferError(
                    "MongoDB transaction failed"
                ) from exc

    def _execute_transfer(
        self,
        session: Any,
        *,
        from_account: str,
        to_account: str,
        amount: Decimal,
    ) -> None:
        """Execute the transfer inside an active MongoDB transaction."""
        source = self._accounts.find_one(
            {"_id": from_account},
            session=session,
            projection={"_id": 1},
        )

        if source is None:
            raise AccountNotFoundError(
                f"source account not found: {from_account}"
            )

        destination = self._accounts.find_one(
            {"_id": to_account},
            session=session,
            projection={"_id": 1},
        )

        if destination is None:
            raise AccountNotFoundError(
                f"destination account not found: {to_account}"
            )

        amount_value = float(amount)

        source_result = self._accounts.update_one(
            {
                "_id": from_account,
                "balance": {"$gte": amount_value},
            },
            {
                "$inc": {"balance": -amount_value},
            },
            session=session,
        )

        if source_result.modified_count != 1:
            raise InsufficientFundsError(
                f"insufficient funds in account: {from_account}"
            )

        destination_result = self._accounts.update_one(
            {"_id": to_account},
            {
                "$inc": {"balance": amount_value},
            },
            session=session,
        )

        if destination_result.modified_count != 1:
            raise AccountNotFoundError(
                f"destination account not found: {to_account}"
            )

    @staticmethod
    def _validate_transfer(
        *,
        from_account: str,
        to_account: str,
        amount: Decimal,
    ) -> None:
        """Validate transfer input before opening a database transaction."""
        if not from_account.strip():
            raise ValueError("from_account must not be empty")

        if not to_account.strip():
            raise ValueError("to_account must not be empty")

        if from_account == to_account:
            raise ValueError(
                "source and destination accounts must be different"
            )

        if amount <= Decimal("0"):
            raise ValueError("amount must be greater than zero")

        if not amount.is_finite():
            raise ValueError("amount must be finite")