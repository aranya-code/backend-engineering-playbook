from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from bson import ObjectId
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult

from src.repositories.user_repository import UserRepository


@pytest.fixture
def collection() -> MagicMock:
    """Provide an isolated mock MongoDB collection."""
    return MagicMock()


@pytest.fixture
def repository(collection: MagicMock) -> UserRepository:
    """Create a repository backed by the mocked collection."""
    return UserRepository(collection)


def test_create_inserts_user_and_returns_id(
    repository: UserRepository,
    collection: MagicMock,
) -> None:
    """Creating a user should insert a normalized document and return its ID."""
    user_id = ObjectId()
    collection.insert_one.return_value = InsertOneResult(user_id, acknowledged=True)

    result = repository.create(
        name=" Alice ",
        email=" ALICE@example.com ",
    )

    assert result == user_id

    inserted_document = collection.insert_one.call_args.args[0]

    assert inserted_document["_id"] == user_id
    assert inserted_document["name"] == "Alice"
    assert inserted_document["email"] == "alice@example.com"
    assert inserted_document["active"] is True
    assert "created_at" in inserted_document
    assert "updated_at" in inserted_document


def test_get_by_id_returns_matching_user(
    repository: UserRepository,
    collection: MagicMock,
) -> None:
    """The repository should query users by ObjectId."""
    user_id = ObjectId()
    expected_user = {
        "_id": user_id,
        "name": "Alice",
        "email": "alice@example.com",
        "active": True,
    }
    collection.find_one.return_value = expected_user

    result = repository.get_by_id(user_id)

    assert result == expected_user
    collection.find_one.assert_called_once_with({"_id": user_id})


def test_get_by_id_returns_none_when_user_does_not_exist(
    repository: UserRepository,
    collection: MagicMock,
) -> None:
    """A missing user should be represented by None."""
    user_id = ObjectId()
    collection.find_one.return_value = None

    result = repository.get_by_id(user_id)

    assert result is None
    collection.find_one.assert_called_once_with({"_id": user_id})


def test_get_by_email_normalizes_email(
    repository: UserRepository,
    collection: MagicMock,
) -> None:
    """Email lookups should use the same normalization as user creation."""
    expected_user = {
        "_id": ObjectId(),
        "name": "Alice",
        "email": "alice@example.com",
        "active": True,
    }
    collection.find_one.return_value = expected_user

    result = repository.get_by_email(" ALICE@example.com ")

    assert result == expected_user
    collection.find_one.assert_called_once_with(
        {"email": "alice@example.com"},
    )


def test_list_users_returns_bounded_page(
    repository: UserRepository,
    collection: MagicMock,
) -> None:
    """User listing should apply filtering, sorting, offset, and limit."""
    users = [
        {"_id": ObjectId(), "name": "Alice", "active": True},
        {"_id": ObjectId(), "name": "Bob", "active": True},
    ]

    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.__iter__.return_value = iter(users)

    collection.find.return_value = cursor

    result = repository.list_users(
        active=True,
        skip=20,
        limit=10,
    )

    assert result == users
    collection.find.assert_called_once_with({"active": True})
    cursor.sort.assert_called_once_with("_id", 1)
    cursor.skip.assert_called_once_with(20)
    cursor.limit.assert_called_once_with(10)


def test_list_users_without_filter_uses_empty_query(
    repository: UserRepository,
    collection: MagicMock,
) -> None:
    """Listing all users should use an empty MongoDB filter."""
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.__iter__.return_value = iter([])

    collection.find.return_value = cursor

    result = repository.list_users()

    assert result == []
    collection.find.assert_called_once_with({})
    cursor.sort.assert_called_once_with("_id", 1)
    cursor.skip.assert_called_once_with(0)
    cursor.limit.assert_called_once_with(20)


@pytest.mark.parametrize(
    ("skip", "limit", "message"),
    [
        (-1, 20, "skip must be greater than or equal to zero"),
        (0, 0, "limit must be greater than zero"),
        (0, -1, "limit must be greater than zero"),
    ],
)
def test_list_users_rejects_invalid_pagination(
    repository: UserRepository,
    skip: int,
    limit: int,
    message: str,
) -> None:
    """Invalid pagination parameters should fail before querying MongoDB."""
    with pytest.raises(ValueError, match=message):
        repository.list_users(skip=skip, limit=limit)


def test_update_updates_user_fields(
    repository: UserRepository,
    collection: MagicMock,
) -> None:
    """Updating a user should use a targeted $set update."""
    user_id = ObjectId()
    update_result = UpdateResult(
        {
            "n": 1,
            "nModified": 1,
            "updatedExisting": True,
        },
        acknowledged=True,
    )
    collection.update_one.return_value = update_result

    result = repository.update(
        user_id,
        name="Alice Updated",
        active=False,
    )

    assert result is update_result
    collection.update_one.assert_called_once()

    query, update = collection.update_one.call_args.args

    assert query == {"_id": user_id}
    assert update["$set"]["name"] == "Alice Updated"
    assert update["$set"]["active"] is False
    assert "updated_at" in update["$set"]


def test_update_raises_for_empty_name(
    repository: UserRepository,
    collection: MagicMock,
) -> None:
    """Invalid user data should be rejected before reaching MongoDB."""
    user_id = ObjectId()

    with pytest.raises(ValueError, match="name must not be empty"):
        repository.update(user_id, name="   ")

    collection.update_one.assert_not_called()


def test_delete_removes_user(
    repository: UserRepository,
    collection: MagicMock,
) -> None:
    """Deleting a user should target the document by ObjectId."""
    user_id = ObjectId()
    delete_result = DeleteResult(
        {
            "n": 1,
            "ok": 1,
        },
        acknowledged=True,
    )
    collection.delete_one.return_value = delete_result

    result = repository.delete(user_id)

    assert result is delete_result
    collection.delete_one.assert_called_once_with({"_id": user_id})

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from bson import ObjectId
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult

from src.repositories.user_repository import UserRepository


@pytest.fixture
def collection() -> MagicMock:
    """Provide an isolated mock MongoDB collection."""
    return MagicMock()


@pytest.fixture
def repository(collection: MagicMock) -> UserRepository:
    """Create a repository backed by the mocked collection."""
    return UserRepository(collection)


def test_create_inserts_user_and_returns_id(
    repository: UserRepository,
    collection: MagicMock,
) -> None:
    """Creating a user should insert a normalized document and return its ID."""
    user_id = ObjectId()
    collection.insert_one.return_value = InsertOneResult(user_id, acknowledged=True)

    result = repository.create(
        name=" Alice ",
        email=" ALICE@example.com ",
    )

    assert result == user_id

    inserted_document = collection.insert_one.call_args.args[0]

    assert inserted_document["_id"] == user_id
    assert inserted_document["name"] == "Alice"
    assert inserted_document["email"] == "alice@example.com"
    assert inserted_document["active"] is True
    assert "created_at" in inserted_document
    assert "updated_at" in inserted_document


def test_get_by_id_returns_matching_user(
    repository: UserRepository,
    collection: MagicMock,
) -> None:
    """The repository should query users by ObjectId."""
    user_id = ObjectId()
    expected_user = {
        "_id": user_id,
        "name": "Alice",
        "email": "alice@example.com",
        "active": True,
    }
    collection.find_one.return_value = expected_user

    result = repository.get_by_id(user_id)

    assert result == expected_user
    collection.find_one.assert_called_once_with({"_id": user_id})


def test_get_by_id_returns_none_when_user_does_not_exist(
    repository: UserRepository,
    collection: MagicMock,
) -> None:
    """A missing user should be represented by None."""
    user_id = ObjectId()
    collection.find_one.return_value = None

    result = repository.get_by_id(user_id)

    assert result is None
    collection.find_one.assert_called_once_with({"_id": user_id})


def test_get_by_email_normalizes_email(
    repository: UserRepository,
    collection: MagicMock,
) -> None:
    """Email lookups should use the same normalization as user creation."""
    expected_user = {
        "_id": ObjectId(),
        "name": "Alice",
        "email": "alice@example.com",
        "active": True,
    }
    collection.find_one.return_value = expected_user

    result = repository.get_by_email(" ALICE@example.com ")

    assert result == expected_user
    collection.find_one.assert_called_once_with(
        {"email": "alice@example.com"},
    )


def test_list_users_returns_bounded_page(
    repository: UserRepository,
    collection: MagicMock,
) -> None:
    """User listing should apply filtering, sorting, offset, and limit."""
    users = [
        {"_id": ObjectId(), "name": "Alice", "active": True},
        {"_id": ObjectId(), "name": "Bob", "active": True},
    ]

    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.__iter__.return_value = iter(users)

    collection.find.return_value = cursor

    result = repository.list_users(
        active=True,
        skip=20,
        limit=10,
    )

    assert result == users
    collection.find.assert_called_once_with({"active": True})
    cursor.sort.assert_called_once_with("_id", 1)
    cursor.skip.assert_called_once_with(20)
    cursor.limit.assert_called_once_with(10)


def test_list_users_without_filter_uses_empty_query(
    repository: UserRepository,
    collection: MagicMock,
) -> None:
    """Listing all users should use an empty MongoDB filter."""
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.__iter__.return_value = iter([])

    collection.find.return_value = cursor

    result = repository.list_users()

    assert result == []
    collection.find.assert_called_once_with({})
    cursor.sort.assert_called_once_with("_id", 1)
    cursor.skip.assert_called_once_with(0)
    cursor.limit.assert_called_once_with(20)


@pytest.mark.parametrize(
    ("skip", "limit", "message"),
    [
        (-1, 20, "skip must be greater than or equal to zero"),
        (0, 0, "limit must be greater than zero"),
        (0, -1, "limit must be greater than zero"),
    ],
)
def test_list_users_rejects_invalid_pagination(
    repository: UserRepository,
    skip: int,
    limit: int,
    message: str,
) -> None:
    """Invalid pagination parameters should fail before querying MongoDB."""
    with pytest.raises(ValueError, match=message):
        repository.list_users(skip=skip, limit=limit)


def test_update_updates_user_fields(
    repository: UserRepository,
    collection: MagicMock,
) -> None:
    """Updating a user should use a targeted $set update."""
    user_id = ObjectId()
    update_result = UpdateResult(
        {
            "n": 1,
            "nModified": 1,
            "updatedExisting": True,
        },
        acknowledged=True,
    )
    collection.update_one.return_value = update_result

    result = repository.update(
        user_id,
        name="Alice Updated",
        active=False,
    )

    assert result is update_result
    collection.update_one.assert_called_once()

    query, update = collection.update_one.call_args.args

    assert query == {"_id": user_id}
    assert update["$set"]["name"] == "Alice Updated"
    assert update["$set"]["active"] is False
    assert "updated_at" in update["$set"]


def test_update_raises_for_empty_name(
    repository: UserRepository,
    collection: MagicMock,
) -> None:
    """Invalid user data should be rejected before reaching MongoDB."""
    user_id = ObjectId()

    with pytest.raises(ValueError, match="name must not be empty"):
        repository.update(user_id, name="   ")

    collection.update_one.assert_not_called()


def test_delete_removes_user(
    repository: UserRepository,
    collection: MagicMock,
) -> None:
    """Deleting a user should target the document by ObjectId."""
    user_id = ObjectId()
    delete_result = DeleteResult(
        {
            "n": 1,
            "ok": 1,
        },
        acknowledged=True,
    )
    collection.delete_one.return_value = delete_result

    result = repository.delete(user_id)

    assert result is delete_result
    collection.delete_one.assert_called_once_with({"_id": user_id})