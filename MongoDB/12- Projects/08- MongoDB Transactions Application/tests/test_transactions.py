"""Tests for MongoDB account transfer transactions."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from services.transfer_service import (
    AccountNotFoundError,
    InsufficientFundsError,
    TransferError,
    TransferService,
)


class FakeSession:
    """Minimal session implementation for unit-testing transaction flow."""

    def __init__(self) -> None:
        self.with_transaction_calls = 0
        self.callback = None

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def with_transaction(self, callback, **kwargs) -> None:
        self.with_transaction_calls += 1
        self.callback = callback
        callback(self)


class FakeClient:
    """Minimal MongoDB client double used by service-level tests."""

    def __init__(self, accounts: MagicMock) -> None:
        self.database = MagicMock()
        self.database.get_collection.return_value = accounts
        self.session = FakeSession()

    def __getitem__(self, database_name: str) -> MagicMock:
        return self.database

    def start_session(self) -> FakeSession:
        return self.session


def build_service(
    *,
    source_exists: bool = True,
    destination_exists: bool = True,
    source_modified: int = 1,
    destination_modified: int = 1,
) -> tuple[TransferService, MagicMock, FakeSession]:
    """Build a transfer service with a controlled MongoDB double."""
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

    client = FakeClient(accounts)
    service = TransferService(
        client,
        database_name="mongodb_transactions",
    )

    return service, accounts, client.session


def test_transfer_commits_successfully() -> None:
    """A valid transfer updates both accounts inside one transaction."""
    service, accounts, session = build_service()

    service.transfer(
        from_account="account-001",
        to_account="account-002",
        amount=Decimal("100.00"),
    )

    assert session.with_transaction_calls == 1
    assert accounts.find_one.call_count == 2
    assert accounts.update_one.call_count == 2

    source_filter = accounts.update_one.call_args_list[0].args[0]
    source_update = accounts.update_one.call_args_list[0].args[1]

    assert source_filter == {
        "_id": "account-001",
        "balance": {"$gte": 100.0},
    }
    assert source_update == {
        "$inc": {"balance": -100.0},
    }
    assert accounts.update_one.call_args_list[0].kwargs == {
        "session": session,
    }

    destination_filter = accounts.update_one.call_args_list[1].args[0]
    destination_update = accounts.update_one.call_args_list[1].args[1]

    assert destination_filter == {"_id": "account-002"}
    assert destination_update == {
        "$inc": {"balance": 100.0},
    }
    assert accounts.update_one.call_args_list[1].kwargs == {
        "session": session,
    }


def test_transfer_rejects_non_positive_amount() -> None:
    """Transfers with zero or negative amounts are rejected."""
    service, accounts, session = build_service()

    with pytest.raises(ValueError, match="greater than zero"):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("0"),
        )

    assert session.with_transaction_calls == 0
    accounts.find_one.assert_not_called()
    accounts.update_one.assert_not_called()


def test_transfer_rejects_non_finite_amount() -> None:
    """NaN and infinite monetary values are rejected."""
    service, accounts, session = build_service()

    with pytest.raises(ValueError, match="finite"):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("NaN"),
        )

    assert session.with_transaction_calls == 0
    accounts.find_one.assert_not_called()


@pytest.mark.parametrize(
    ("from_account", "to_account"),
    [
        ("", "account-002"),
        ("   ", "account-002"),
        ("account-001", ""),
        ("account-001", "   "),
    ],
)
def test_transfer_rejects_empty_account_identifiers(
    from_account: str,
    to_account: str,
) -> None:
    """Account identifiers must contain meaningful values."""
    service, accounts, session = build_service()

    with pytest.raises(ValueError, match="must not be empty"):
        service.transfer(
            from_account=from_account,
            to_account=to_account,
            amount=Decimal("100"),
        )

    assert session.with_transaction_calls == 0
    accounts.find_one.assert_not_called()


def test_transfer_rejects_same_source_and_destination() -> None:
    """A transfer cannot use the same account as both endpoints."""
    service, accounts, session = build_service()

    with pytest.raises(ValueError, match="different"):
        service.transfer(
            from_account="account-001",
            to_account="account-001",
            amount=Decimal("100"),
        )

    assert session.with_transaction_calls == 0
    accounts.find_one.assert_not_called()


def test_transfer_fails_when_source_account_does_not_exist() -> None:
    """A missing source account aborts the transfer before updates."""
    service, accounts, session = build_service(
        source_exists=False,
    )

    with pytest.raises(AccountNotFoundError, match="source account"):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("100"),
        )

    assert session.with_transaction_calls == 1
    accounts.update_one.assert_not_called()


def test_transfer_fails_when_destination_account_does_not_exist() -> None:
    """A missing destination account prevents either balance update."""
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

    assert session.with_transaction_calls == 1
    accounts.update_one.assert_not_called()


def test_transfer_fails_when_source_balance_condition_is_not_met() -> None:
    """The conditional source update prevents an overdraft."""
    service, accounts, session = build_service(
        source_modified=0,
    )

    with pytest.raises(InsufficientFundsError, match="insufficient funds"):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("100"),
        )

    assert session.with_transaction_calls == 1
    assert accounts.update_one.call_count == 1


def test_transfer_fails_when_destination_update_does_not_modify() -> None:
    """A failed destination update causes the transaction to fail."""
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

    assert session.with_transaction_calls == 1
    assert accounts.update_one.call_count == 2


def test_transfer_uses_majority_write_concern() -> None:
    """The transaction requests majority write acknowledgement."""
    service, _, session = build_service()

    service.transfer(
        from_account="account-001",
        to_account="account-002",
        amount=Decimal("25.50"),
    )

    assert session.with_transaction_calls == 1
    assert session.callback is not None


def test_transfer_wraps_mongodb_errors() -> None:
    """Unexpected PyMongo errors are exposed as TransferError."""
    accounts = MagicMock()
    accounts.find_one.side_effect = RuntimeError("database unavailable")

    client = FakeClient(accounts)
    service = TransferService(
        client,
        database_name="mongodb_transactions",
    )

    with pytest.raises(RuntimeError, match="database unavailable"):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("100"),
        )


def test_transaction_callback_receives_session() -> None:
    """MongoDB operations receive the active transaction session."""
    service, accounts, session = build_service()

    service.transfer(
        from_account="account-001",
        to_account="account-002",
        amount=Decimal("10"),
    )

    for call in accounts.find_one.call_args_list:
        assert call.kwargs["session"] is session

    for call in accounts.update_one.call_args_list:
        assert call.kwargs["session"] is session

"""Tests for MongoDB account transfer transactions."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from services.transfer_service import (
    AccountNotFoundError,
    InsufficientFundsError,
    TransferError,
    TransferService,
)


class FakeSession:
    """Minimal session implementation for unit-testing transaction flow."""

    def __init__(self) -> None:
        self.with_transaction_calls = 0
        self.callback = None

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def with_transaction(self, callback, **kwargs) -> None:
        self.with_transaction_calls += 1
        self.callback = callback
        callback(self)


class FakeClient:
    """Minimal MongoDB client double used by service-level tests."""

    def __init__(self, accounts: MagicMock) -> None:
        self.database = MagicMock()
        self.database.get_collection.return_value = accounts
        self.session = FakeSession()

    def __getitem__(self, database_name: str) -> MagicMock:
        return self.database

    def start_session(self) -> FakeSession:
        return self.session


def build_service(
    *,
    source_exists: bool = True,
    destination_exists: bool = True,
    source_modified: int = 1,
    destination_modified: int = 1,
) -> tuple[TransferService, MagicMock, FakeSession]:
    """Build a transfer service with a controlled MongoDB double."""
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

    client = FakeClient(accounts)
    service = TransferService(
        client,
        database_name="mongodb_transactions",
    )

    return service, accounts, client.session


def test_transfer_commits_successfully() -> None:
    """A valid transfer updates both accounts inside one transaction."""
    service, accounts, session = build_service()

    service.transfer(
        from_account="account-001",
        to_account="account-002",
        amount=Decimal("100.00"),
    )

    assert session.with_transaction_calls == 1
    assert accounts.find_one.call_count == 2
    assert accounts.update_one.call_count == 2

    source_filter = accounts.update_one.call_args_list[0].args[0]
    source_update = accounts.update_one.call_args_list[0].args[1]

    assert source_filter == {
        "_id": "account-001",
        "balance": {"$gte": 100.0},
    }
    assert source_update == {
        "$inc": {"balance": -100.0},
    }
    assert accounts.update_one.call_args_list[0].kwargs == {
        "session": session,
    }

    destination_filter = accounts.update_one.call_args_list[1].args[0]
    destination_update = accounts.update_one.call_args_list[1].args[1]

    assert destination_filter == {"_id": "account-002"}
    assert destination_update == {
        "$inc": {"balance": 100.0},
    }
    assert accounts.update_one.call_args_list[1].kwargs == {
        "session": session,
    }


def test_transfer_rejects_non_positive_amount() -> None:
    """Transfers with zero or negative amounts are rejected."""
    service, accounts, session = build_service()

    with pytest.raises(ValueError, match="greater than zero"):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("0"),
        )

    assert session.with_transaction_calls == 0
    accounts.find_one.assert_not_called()
    accounts.update_one.assert_not_called()


def test_transfer_rejects_non_finite_amount() -> None:
    """NaN and infinite monetary values are rejected."""
    service, accounts, session = build_service()

    with pytest.raises(ValueError, match="finite"):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("NaN"),
        )

    assert session.with_transaction_calls == 0
    accounts.find_one.assert_not_called()


@pytest.mark.parametrize(
    ("from_account", "to_account"),
    [
        ("", "account-002"),
        ("   ", "account-002"),
        ("account-001", ""),
        ("account-001", "   "),
    ],
)
def test_transfer_rejects_empty_account_identifiers(
    from_account: str,
    to_account: str,
) -> None:
    """Account identifiers must contain meaningful values."""
    service, accounts, session = build_service()

    with pytest.raises(ValueError, match="must not be empty"):
        service.transfer(
            from_account=from_account,
            to_account=to_account,
            amount=Decimal("100"),
        )

    assert session.with_transaction_calls == 0
    accounts.find_one.assert_not_called()


def test_transfer_rejects_same_source_and_destination() -> None:
    """A transfer cannot use the same account as both endpoints."""
    service, accounts, session = build_service()

    with pytest.raises(ValueError, match="different"):
        service.transfer(
            from_account="account-001",
            to_account="account-001",
            amount=Decimal("100"),
        )

    assert session.with_transaction_calls == 0
    accounts.find_one.assert_not_called()


def test_transfer_fails_when_source_account_does_not_exist() -> None:
    """A missing source account aborts the transfer before updates."""
    service, accounts, session = build_service(
        source_exists=False,
    )

    with pytest.raises(AccountNotFoundError, match="source account"):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("100"),
        )

    assert session.with_transaction_calls == 1
    accounts.update_one.assert_not_called()


def test_transfer_fails_when_destination_account_does_not_exist() -> None:
    """A missing destination account prevents either balance update."""
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

    assert session.with_transaction_calls == 1
    accounts.update_one.assert_not_called()


def test_transfer_fails_when_source_balance_condition_is_not_met() -> None:
    """The conditional source update prevents an overdraft."""
    service, accounts, session = build_service(
        source_modified=0,
    )

    with pytest.raises(InsufficientFundsError, match="insufficient funds"):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("100"),
        )

    assert session.with_transaction_calls == 1
    assert accounts.update_one.call_count == 1


def test_transfer_fails_when_destination_update_does_not_modify() -> None:
    """A failed destination update causes the transaction to fail."""
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

    assert session.with_transaction_calls == 1
    assert accounts.update_one.call_count == 2


def test_transfer_uses_majority_write_concern() -> None:
    """The transaction requests majority write acknowledgement."""
    service, _, session = build_service()

    service.transfer(
        from_account="account-001",
        to_account="account-002",
        amount=Decimal("25.50"),
    )

    assert session.with_transaction_calls == 1
    assert session.callback is not None


def test_transfer_wraps_mongodb_errors() -> None:
    """Unexpected PyMongo errors are exposed as TransferError."""
    accounts = MagicMock()
    accounts.find_one.side_effect = RuntimeError("database unavailable")

    client = FakeClient(accounts)
    service = TransferService(
        client,
        database_name="mongodb_transactions",
    )

    with pytest.raises(RuntimeError, match="database unavailable"):
        service.transfer(
            from_account="account-001",
            to_account="account-002",
            amount=Decimal("100"),
        )


def test_transaction_callback_receives_session() -> None:
    """MongoDB operations receive the active transaction session."""
    service, accounts, session = build_service()

    service.transfer(
        from_account="account-001",
        to_account="account-002",
        amount=Decimal("10"),
    )

    for call in accounts.find_one.call_args_list:
        assert call.kwargs["session"] is session

    for call in accounts.update_one.call_args_list:
        assert call.kwargs["session"] is session