from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from src.services.user_service import UserService


@pytest.fixture
def repository() -> MagicMock:
    """Provide an isolated mock repository for service-layer tests."""
    return MagicMock()


@pytest.fixture
def service(repository: MagicMock) -> UserService:
    """Create a user service backed by the mocked repository."""
    return UserService(repository)


def test_create_user_delegates_to_repository(
    service: UserService,
    repository: MagicMock,
) -> None:
    """Creating a user should delegate persistence to the repository."""
    user_id = ObjectId()
    repository.create.return_value = user_id

    result = service.create_user(
        name="Alice",
        email="alice@example.com",
    )

    assert result == user_id
    repository.create.assert_called_once_with(
        name="Alice",
        email="alice@example.com",
    )


def test_create_user_normalizes_input_before_persistence(
    service: UserService,
    repository: MagicMock,
) -> None:
    """The service should normalize user input before calling the repository."""
    user_id = ObjectId()
    repository.create.return_value = user_id

    result = service.create_user(
        name=" Alice ",
        email=" ALICE@example.com ",
    )

    assert result == user_id
    repository.create.assert_called_once_with(
        name="Alice",
        email="alice@example.com",
    )


@pytest.mark.parametrize(
    ("name", "email", "message"),
    [
        ("", "alice@example.com", "name must not be empty"),
        ("   ", "alice@example.com", "name must not be empty"),
        ("Alice", "", "email must not be empty"),
        ("Alice", "   ", "email must not be empty"),
    ],
)
def test_create_user_rejects_invalid_input(
    service: UserService,
    repository: MagicMock,
    name: str,
    email: str,
    message: str,
) -> None:
    """Invalid user data should be rejected before persistence."""
    with pytest.raises(ValueError, match=message):
        service.create_user(name=name, email=email)

    repository.create.assert_not_called()


def test_create_user_translates_duplicate_email_error(
    service: UserService,
    repository: MagicMock,
) -> None:
    """A duplicate MongoDB key should become a service-level conflict."""
    repository.create.side_effect = DuplicateKeyError(
        "E11000 duplicate key error collection: crud_app.users index: "
        "idx_users_email_unique dup key: { email: \"alice@example.com\" }"
    )

    with pytest.raises(ValueError, match="email already exists"):
        service.create_user(
            name="Alice",
            email="alice@example.com",
        )


def test_get_user_returns_repository_result(
    service: UserService,
    repository: MagicMock,
) -> None:
    """Fetching a user should return the repository result unchanged."""
    user_id = ObjectId()
    expected_user = {
        "_id": user_id,
        "name": "Alice",
        "email": "alice@example.com",
        "active": True,
    }
    repository.get_by_id.return_value = expected_user

    result = service.get_user(user_id)

    assert result == expected_user
    repository.get_by_id.assert_called_once_with(user_id)


def test_get_user_returns_none_when_repository_finds_nothing(
    service: UserService,
    repository: MagicMock,
) -> None:
    """A missing user should remain a repository-level None result."""
    user_id = ObjectId()
    repository.get_by_id.return_value = None

    result = service.get_user(user_id)

    assert result is None
    repository.get_by_id.assert_called_once_with(user_id)


def test_get_user_by_email_normalizes_email(
    service: UserService,
    repository: MagicMock,
) -> None:
    """Email lookups should normalize the email before repository access."""
    expected_user = {
        "_id": ObjectId(),
        "name": "Alice",
        "email": "alice@example.com",
        "active": True,
    }
    repository.get_by_email.return_value = expected_user

    result = service.get_user_by_email(" ALICE@example.com ")

    assert result == expected_user
    repository.get_by_email.assert_called_once_with("alice@example.com")


def test_get_user_by_email_rejects_empty_email(
    service: UserService,
    repository: MagicMock,
) -> None:
    """An empty email should fail without querying MongoDB."""
    with pytest.raises(ValueError, match="email must not be empty"):
        service.get_user_by_email("   ")

    repository.get_by_email.assert_not_called()


def test_list_users_delegates_pagination_and_filtering(
    service: UserService,
    repository: MagicMock,
) -> None:
    """Listing users should pass validated pagination and filters downstream."""
    expected_users = [
        {
            "_id": ObjectId(),
            "name": "Alice",
            "email": "alice@example.com",
            "active": True,
        }
    ]
    repository.list_users.return_value = expected_users

    result = service.list_users(
        active=True,
        skip=20,
        limit=10,
    )

    assert result == expected_users
    repository.list_users.assert_called_once_with(
        active=True,
        skip=20,
        limit=10,
    )


@pytest.mark.parametrize(
    ("skip", "limit", "message"),
    [
        (-1, 20, "skip must be greater than or equal to zero"),
        (0, 0, "limit must be greater than zero"),
        (0, -1, "limit must be greater than zero"),
    ],
)
def test_list_users_rejects_invalid_pagination(
    service: UserService,
    repository: MagicMock,
    skip: int,
    limit: int,
    message: str,
) -> None:
    """Invalid pagination must be rejected before repository access."""
    with pytest.raises(ValueError, match=message):
        service.list_users(
            skip=skip,
            limit=limit,
        )

    repository.list_users.assert_not_called()


def test_update_user_delegates_changes_to_repository(
    service: UserService,
    repository: MagicMock,
) -> None:
    """Updating a user should pass only requested changes to the repository."""
    user_id = ObjectId()
    repository.update.return_value = MagicMock(matched_count=1)

    result = service.update_user(
        user_id,
        name="Alice Updated",
        active=False,
    )

    assert result is repository.update.return_value
    repository.update.assert_called_once_with(
        user_id,
        name="Alice Updated",
        active=False,
    )


def test_update_user_rejects_empty_name(
    service: UserService,
    repository: MagicMock,
) -> None:
    """An empty updated name should fail before persistence."""
    user_id = ObjectId()

    with pytest.raises(ValueError, match="name must not be empty"):
        service.update_user(
            user_id,
            name="   ",
        )

    repository.update.assert_not_called()


def test_update_user_normalizes_name_and_email(
    service: UserService,
    repository: MagicMock,
) -> None:
    """Updated string fields should be normalized before persistence."""
    user_id = ObjectId()
    repository.update.return_value = MagicMock(matched_count=1)

    service.update_user(
        user_id,
        name=" Alice Updated ",
        email=" ALICE@EXAMPLE.COM ",
    )

    repository.update.assert_called_once_with(
        user_id,
        name="Alice Updated",
        email="alice@example.com",
    )


def test_delete_user_delegates_to_repository(
    service: UserService,
    repository: MagicMock,
) -> None:
    """Deleting a user should delegate deletion to the repository."""
    user_id = ObjectId()
    repository.delete.return_value = MagicMock(deleted_count=1)

    result = service.delete_user(user_id)

    assert result is repository.delete.return_value
    repository.delete.assert_called_once_with(user_id)


def test_delete_user_returns_not_found_for_missing_user(
    service: UserService,
    repository: MagicMock,
) -> None:
    """A delete operation affecting no documents should remain distinguishable."""
    user_id = ObjectId()
    repository.delete.return_value = MagicMock(deleted_count=0)

    result = service.delete_user(user_id)

    assert result.deleted_count == 0
    repository.delete.assert_called_once_with(user_id)

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from src.services.user_service import UserService


@pytest.fixture
def repository() -> MagicMock:
    """Provide an isolated mock repository for service-layer tests."""
    return MagicMock()


@pytest.fixture
def service(repository: MagicMock) -> UserService:
    """Create a user service backed by the mocked repository."""
    return UserService(repository)


def test_create_user_delegates_to_repository(
    service: UserService,
    repository: MagicMock,
) -> None:
    """Creating a user should delegate persistence to the repository."""
    user_id = ObjectId()
    repository.create.return_value = user_id

    result = service.create_user(
        name="Alice",
        email="alice@example.com",
    )

    assert result == user_id
    repository.create.assert_called_once_with(
        name="Alice",
        email="alice@example.com",
    )


def test_create_user_normalizes_input_before_persistence(
    service: UserService,
    repository: MagicMock,
) -> None:
    """The service should normalize user input before calling the repository."""
    user_id = ObjectId()
    repository.create.return_value = user_id

    result = service.create_user(
        name=" Alice ",
        email=" ALICE@example.com ",
    )

    assert result == user_id
    repository.create.assert_called_once_with(
        name="Alice",
        email="alice@example.com",
    )


@pytest.mark.parametrize(
    ("name", "email", "message"),
    [
        ("", "alice@example.com", "name must not be empty"),
        ("   ", "alice@example.com", "name must not be empty"),
        ("Alice", "", "email must not be empty"),
        ("Alice", "   ", "email must not be empty"),
    ],
)
def test_create_user_rejects_invalid_input(
    service: UserService,
    repository: MagicMock,
    name: str,
    email: str,
    message: str,
) -> None:
    """Invalid user data should be rejected before persistence."""
    with pytest.raises(ValueError, match=message):
        service.create_user(name=name, email=email)

    repository.create.assert_not_called()


def test_create_user_translates_duplicate_email_error(
    service: UserService,
    repository: MagicMock,
) -> None:
    """A duplicate MongoDB key should become a service-level conflict."""
    repository.create.side_effect = DuplicateKeyError(
        "E11000 duplicate key error collection: crud_app.users index: "
        "idx_users_email_unique dup key: { email: \"alice@example.com\" }"
    )

    with pytest.raises(ValueError, match="email already exists"):
        service.create_user(
            name="Alice",
            email="alice@example.com",
        )


def test_get_user_returns_repository_result(
    service: UserService,
    repository: MagicMock,
) -> None:
    """Fetching a user should return the repository result unchanged."""
    user_id = ObjectId()
    expected_user = {
        "_id": user_id,
        "name": "Alice",
        "email": "alice@example.com",
        "active": True,
    }
    repository.get_by_id.return_value = expected_user

    result = service.get_user(user_id)

    assert result == expected_user
    repository.get_by_id.assert_called_once_with(user_id)


def test_get_user_returns_none_when_repository_finds_nothing(
    service: UserService,
    repository: MagicMock,
) -> None:
    """A missing user should remain a repository-level None result."""
    user_id = ObjectId()
    repository.get_by_id.return_value = None

    result = service.get_user(user_id)

    assert result is None
    repository.get_by_id.assert_called_once_with(user_id)


def test_get_user_by_email_normalizes_email(
    service: UserService,
    repository: MagicMock,
) -> None:
    """Email lookups should normalize the email before repository access."""
    expected_user = {
        "_id": ObjectId(),
        "name": "Alice",
        "email": "alice@example.com",
        "active": True,
    }
    repository.get_by_email.return_value = expected_user

    result = service.get_user_by_email(" ALICE@example.com ")

    assert result == expected_user
    repository.get_by_email.assert_called_once_with("alice@example.com")


def test_get_user_by_email_rejects_empty_email(
    service: UserService,
    repository: MagicMock,
) -> None:
    """An empty email should fail without querying MongoDB."""
    with pytest.raises(ValueError, match="email must not be empty"):
        service.get_user_by_email("   ")

    repository.get_by_email.assert_not_called()


def test_list_users_delegates_pagination_and_filtering(
    service: UserService,
    repository: MagicMock,
) -> None:
    """Listing users should pass validated pagination and filters downstream."""
    expected_users = [
        {
            "_id": ObjectId(),
            "name": "Alice",
            "email": "alice@example.com",
            "active": True,
        }
    ]
    repository.list_users.return_value = expected_users

    result = service.list_users(
        active=True,
        skip=20,
        limit=10,
    )

    assert result == expected_users
    repository.list_users.assert_called_once_with(
        active=True,
        skip=20,
        limit=10,
    )


@pytest.mark.parametrize(
    ("skip", "limit", "message"),
    [
        (-1, 20, "skip must be greater than or equal to zero"),
        (0, 0, "limit must be greater than zero"),
        (0, -1, "limit must be greater than zero"),
    ],
)
def test_list_users_rejects_invalid_pagination(
    service: UserService,
    repository: MagicMock,
    skip: int,
    limit: int,
    message: str,
) -> None:
    """Invalid pagination must be rejected before repository access."""
    with pytest.raises(ValueError, match=message):
        service.list_users(
            skip=skip,
            limit=limit,
        )

    repository.list_users.assert_not_called()


def test_update_user_delegates_changes_to_repository(
    service: UserService,
    repository: MagicMock,
) -> None:
    """Updating a user should pass only requested changes to the repository."""
    user_id = ObjectId()
    repository.update.return_value = MagicMock(matched_count=1)

    result = service.update_user(
        user_id,
        name="Alice Updated",
        active=False,
    )

    assert result is repository.update.return_value
    repository.update.assert_called_once_with(
        user_id,
        name="Alice Updated",
        active=False,
    )


def test_update_user_rejects_empty_name(
    service: UserService,
    repository: MagicMock,
) -> None:
    """An empty updated name should fail before persistence."""
    user_id = ObjectId()

    with pytest.raises(ValueError, match="name must not be empty"):
        service.update_user(
            user_id,
            name="   ",
        )

    repository.update.assert_not_called()


def test_update_user_normalizes_name_and_email(
    service: UserService,
    repository: MagicMock,
) -> None:
    """Updated string fields should be normalized before persistence."""
    user_id = ObjectId()
    repository.update.return_value = MagicMock(matched_count=1)

    service.update_user(
        user_id,
        name=" Alice Updated ",
        email=" ALICE@EXAMPLE.COM ",
    )

    repository.update.assert_called_once_with(
        user_id,
        name="Alice Updated",
        email="alice@example.com",
    )


def test_delete_user_delegates_to_repository(
    service: UserService,
    repository: MagicMock,
) -> None:
    """Deleting a user should delegate deletion to the repository."""
    user_id = ObjectId()
    repository.delete.return_value = MagicMock(deleted_count=1)

    result = service.delete_user(user_id)

    assert result is repository.delete.return_value
    repository.delete.assert_called_once_with(user_id)


def test_delete_user_returns_not_found_for_missing_user(
    service: UserService,
    repository: MagicMock,
) -> None:
    """A delete operation affecting no documents should remain distinguishable."""
    user_id = ObjectId()
    repository.delete.return_value = MagicMock(deleted_count=0)

    result = service.delete_user(user_id)

    assert result.deleted_count == 0
    repository.delete.assert_called_once_with(user_id)