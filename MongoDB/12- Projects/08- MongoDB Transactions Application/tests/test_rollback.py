"""Tests for MongoDB transaction rollback behavior."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from pymongo.errors import PyMongoError

from services.transfer_service import (
    AccountNotFoundError,
    InsufficientFundsError,
    TransferError,
    TransferService,
)


class TransactionSession:
    """Test session that records transaction state and supports rollback."""

    def __init__(self) -> None:
        self.transaction_started = False
        self.transaction_aborted = False
        self.transaction_committed = False
        self.callback = None

    def __enter__(self) -> "TransactionSession":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def with_transaction(self, callback, **kwargs) -> None:
        """Execute the callback and model commit or abort semantics."""
        self.transaction_started = True
        self.callback = callback

        try:
            callback(self)
        except Exception:
            self.transaction_aborted = True
            raise
        else:
            self.transaction_committed = True


class TransactionClient:
    """Minimal MongoDB client double for rollback-focused tests."""

    def __init__(self, accounts: MagicMock) -> None:
        self.accounts = accounts
        self.session = TransactionSession()
        self.database = MagicMock()
        self.database.get_collection.return_value = accounts

    def __getitem__(self, database_name: str) -> MagicMock:
        return self.database

    def start_session(self) -> TransactionSession:
        return self.session


def build_service(
    *,
    source_exists: bool = True,
    destination_exists: bool = True,
    source_modified: int = 1,
    destination_modified: int = 1,
) -> tuple[TransferService, MagicMock, TransactionSession]:
    """Create a transfer service backed by deterministic MongoDB doubles."""
    accounts = MagicMock()

    accounts.find_one.side_effect = [
        {"_id": "account-001"} if source_exists else None,
        {"_id": "account-002"} if destination_exists else None,
    ]

    source_result = MagicMock()
    source_result.modified_count = source_modified

    destination_result = MagicMock()
    destination_result.modified_count = destination_modified

    accounts.update_one.side_effect = [
        source_result,
        destination_result,
    ]

    client = TransactionClient(accounts)

    service = TransferService(
        client,
        database_name="mongodb_transactions",
    )

    return service, accounts, client.session


def test_successful_transfer_commits_transaction() -> None:
    """A successful transfer commits rather than rolling back."""
    service, _, session = build_service()

    service.transfer(
        from_account="account-001",
        to_account="account-002",
        amount=Decimal("100"),
    )

    assert session.transaction_started is True
    assert session.transaction_aborted is False
    assert session.transaction_committed is True


def test_insufficient_funds_rolls_back_transaction() -> None:
    """A failed source update aborts the entire transaction."""
    service, accounts, session = build_service(
        source_modified=0,
    )

    with pytest.raises(
        InsufficientFundsError,
        match="insufficient funds",
    ):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("100"),
        )

    assert session.transaction_started is True
    assert session.transaction_aborted is True
    assert session.transaction_committed is False

    # The destination must never be updated after the source update fails.
    assert accounts.update_one.call_count == 1


def test_missing_source_account_rolls_back_transaction() -> None:
    """A missing source account aborts the transaction."""
    service, accounts, session = build_service(
        source_exists=False,
    )

    with pytest.raises(
        AccountNotFoundError,
        match="source account",
    ):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("100"),
        )

    assert session.transaction_started is True
    assert session.transaction_aborted is True
    assert session.transaction_committed is False
    accounts.update_one.assert_not_called()


def test_missing_destination_account_rolls_back_transaction() -> None:
    """A missing destination account prevents any balance updates."""
    service, accounts, session = build_service(
        destination_exists=False,
    )

    with pytest.raises(
        AccountNotFoundError,
        match="destination account",
    ):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("100"),
        )

    assert session.transaction_started is True
    assert session.transaction_aborted is True
    assert session.transaction_committed is False
    accounts.update_one.assert_not_called()


def test_destination_failure_rolls_back_after_source_update() -> None:
    """A destination failure aborts after the source update attempt."""
    service, accounts, session = build_service(
        destination_modified=0,
    )

    with pytest.raises(
        AccountNotFoundError,
        match="destination account",
    ):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("100"),
        )

    assert session.transaction_started is True
    assert session.transaction_aborted is True
    assert session.transaction_committed is False

    # Both operations were attempted inside the same transaction.
    assert accounts.update_one.call_count == 2

    for call in accounts.update_one.call_args_list:
        assert call.kwargs["session"] is session


def test_mongodb_error_rolls_back_transaction() -> None:
    """Unexpected MongoDB failures cause transaction failure."""
    accounts = MagicMock()

    accounts.find_one.side_effect = PyMongoError(
        "simulated database failure"
    )

    client = TransactionClient(accounts)
    service = TransferService(
        client,
        database_name="mongodb_transactions",
    )

    with pytest.raises(TransferError, match="MongoDB transaction failed"):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("100"),
        )

    assert client.session.transaction_started is True
    assert client.session.transaction_aborted is True
    assert client.session.transaction_committed is False


def test_business_error_is_not_converted_to_generic_transfer_error() -> None:
    """Domain errors remain distinguishable from infrastructure failures."""
    service, _, session = build_service(
        source_modified=0,
    )

    with pytest.raises(InsufficientFundsError):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("100"),
        )

    assert session.transaction_aborted is True
    assert session.transaction_committed is False


def test_validation_failure_does_not_start_transaction() -> None:
    """Invalid input is rejected before a MongoDB transaction begins."""
    service, accounts, session = build_service()

    with pytest.raises(ValueError, match="greater than zero"):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("-1"),
        )

    assert session.transaction_started is False
    assert session.transaction_aborted is False
    assert session.transaction_committed is False
    accounts.find_one.assert_not_called()
    accounts.update_one.assert_not_called()


def test_same_account_transfer_does_not_start_transaction() -> None:
    """Invalid self-transfers are rejected before database access."""
    service, accounts, session = build_service()

    with pytest.raises(ValueError, match="different"):
        service.transfer(
            from_account="account-001",
            to_account="account-001",
            amount=Decimal("100"),
        )

    assert session.transaction_started is False
    assert session.transaction_aborted is False
    assert session.transaction_committed is False
    accounts.find_one.assert_not_called()
    accounts.update_one.assert_not_called()


def test_rollback_preserves_single_transaction_session() -> None:
    """All database operations in a failed transfer share one session."""
    service, accounts, session = build_service(
        destination_modified=0,
    )

    with pytest.raises(AccountNotFoundError):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("100"),
        )

    for call in accounts.find_one.call_args_list:
        assert call.kwargs["session"] is session

    for call in accounts.update_one.call_args_list:
        assert call.kwargs["session"] is session

    assert session.transaction_aborted is True
    assert session.transaction_committed is False

"""Tests for MongoDB transaction rollback behavior."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from pymongo.errors import PyMongoError

from services.transfer_service import (
    AccountNotFoundError,
    InsufficientFundsError,
    TransferError,
    TransferService,
)


class TransactionSession:
    """Test session that records transaction state and supports rollback."""

    def __init__(self) -> None:
        self.transaction_started = False
        self.transaction_aborted = False
        self.transaction_committed = False
        self.callback = None

    def __enter__(self) -> "TransactionSession":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def with_transaction(self, callback, **kwargs) -> None:
        """Execute the callback and model commit or abort semantics."""
        self.transaction_started = True
        self.callback = callback

        try:
            callback(self)
        except Exception:
            self.transaction_aborted = True
            raise
        else:
            self.transaction_committed = True


class TransactionClient:
    """Minimal MongoDB client double for rollback-focused tests."""

    def __init__(self, accounts: MagicMock) -> None:
        self.accounts = accounts
        self.session = TransactionSession()
        self.database = MagicMock()
        self.database.get_collection.return_value = accounts

    def __getitem__(self, database_name: str) -> MagicMock:
        return self.database

    def start_session(self) -> TransactionSession:
        return self.session


def build_service(
    *,
    source_exists: bool = True,
    destination_exists: bool = True,
    source_modified: int = 1,
    destination_modified: int = 1,
) -> tuple[TransferService, MagicMock, TransactionSession]:
    """Create a transfer service backed by deterministic MongoDB doubles."""
    accounts = MagicMock()

    accounts.find_one.side_effect = [
        {"_id": "account-001"} if source_exists else None,
        {"_id": "account-002"} if destination_exists else None,
    ]

    source_result = MagicMock()
    source_result.modified_count = source_modified

    destination_result = MagicMock()
    destination_result.modified_count = destination_modified

    accounts.update_one.side_effect = [
        source_result,
        destination_result,
    ]

    client = TransactionClient(accounts)

    service = TransferService(
        client,
        database_name="mongodb_transactions",
    )

    return service, accounts, client.session


def test_successful_transfer_commits_transaction() -> None:
    """A successful transfer commits rather than rolling back."""
    service, _, session = build_service()

    service.transfer(
        from_account="account-001",
        to_account="account-002",
        amount=Decimal("100"),
    )

    assert session.transaction_started is True
    assert session.transaction_aborted is False
    assert session.transaction_committed is True


def test_insufficient_funds_rolls_back_transaction() -> None:
    """A failed source update aborts the entire transaction."""
    service, accounts, session = build_service(
        source_modified=0,
    )

    with pytest.raises(
        InsufficientFundsError,
        match="insufficient funds",
    ):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("100"),
        )

    assert session.transaction_started is True
    assert session.transaction_aborted is True
    assert session.transaction_committed is False

    # The destination must never be updated after the source update fails.
    assert accounts.update_one.call_count == 1


def test_missing_source_account_rolls_back_transaction() -> None:
    """A missing source account aborts the transaction."""
    service, accounts, session = build_service(
        source_exists=False,
    )

    with pytest.raises(
        AccountNotFoundError,
        match="source account",
    ):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("100"),
        )

    assert session.transaction_started is True
    assert session.transaction_aborted is True
    assert session.transaction_committed is False
    accounts.update_one.assert_not_called()


def test_missing_destination_account_rolls_back_transaction() -> None:
    """A missing destination account prevents any balance updates."""
    service, accounts, session = build_service(
        destination_exists=False,
    )

    with pytest.raises(
        AccountNotFoundError,
        match="destination account",
    ):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("100"),
        )

    assert session.transaction_started is True
    assert session.transaction_aborted is True
    assert session.transaction_committed is False
    accounts.update_one.assert_not_called()


def test_destination_failure_rolls_back_after_source_update() -> None:
    """A destination failure aborts after the source update attempt."""
    service, accounts, session = build_service(
        destination_modified=0,
    )

    with pytest.raises(
        AccountNotFoundError,
        match="destination account",
    ):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("100"),
        )

    assert session.transaction_started is True
    assert session.transaction_aborted is True
    assert session.transaction_committed is False

    # Both operations were attempted inside the same transaction.
    assert accounts.update_one.call_count == 2

    for call in accounts.update_one.call_args_list:
        assert call.kwargs["session"] is session


def test_mongodb_error_rolls_back_transaction() -> None:
    """Unexpected MongoDB failures cause transaction failure."""
    accounts = MagicMock()

    accounts.find_one.side_effect = PyMongoError(
        "simulated database failure"
    )

    client = TransactionClient(accounts)
    service = TransferService(
        client,
        database_name="mongodb_transactions",
    )

    with pytest.raises(TransferError, match="MongoDB transaction failed"):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("100"),
        )

    assert client.session.transaction_started is True
    assert client.session.transaction_aborted is True
    assert client.session.transaction_committed is False


def test_business_error_is_not_converted_to_generic_transfer_error() -> None:
    """Domain errors remain distinguishable from infrastructure failures."""
    service, _, session = build_service(
        source_modified=0,
    )

    with pytest.raises(InsufficientFundsError):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("100"),
        )

    assert session.transaction_aborted is True
    assert session.transaction_committed is False


def test_validation_failure_does_not_start_transaction() -> None:
    """Invalid input is rejected before a MongoDB transaction begins."""
    service, accounts, session = build_service()

    with pytest.raises(ValueError, match="greater than zero"):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("-1"),
        )

    assert session.transaction_started is False
    assert session.transaction_aborted is False
    assert session.transaction_committed is False
    accounts.find_one.assert_not_called()
    accounts.update_one.assert_not_called()


def test_same_account_transfer_does_not_start_transaction() -> None:
    """Invalid self-transfers are rejected before database access."""
    service, accounts, session = build_service()

    with pytest.raises(ValueError, match="different"):
        service.transfer(
            from_account="account-001",
            to_account="account-001",
            amount=Decimal("100"),
        )

    assert session.transaction_started is False
    assert session.transaction_aborted is False
    assert session.transaction_committed is False
    accounts.find_one.assert_not_called()
    accounts.update_one.assert_not_called()


def test_rollback_preserves_single_transaction_session() -> None:
    """All database operations in a failed transfer share one session."""
    service, accounts, session = build_service(
        destination_modified=0,
    )

    with pytest.raises(AccountNotFoundError):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("100"),
        )

    for call in accounts.find_one.call_args_list:
        assert call.kwargs["session"] is session

    for call in accounts.update_one.call_args_list:
        assert call.kwargs["session"] is session

    assert session.transaction_aborted is True
    assert session.transaction_committed is False