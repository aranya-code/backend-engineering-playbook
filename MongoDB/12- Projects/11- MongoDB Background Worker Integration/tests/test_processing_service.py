"""Tests for the MongoDB background job processing service."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from pymongo.errors import PyMongoError

from services.processing_service import (
    InvalidJobError,
    ProcessingError,
    ProcessingService,
)


@pytest.fixture
def database() -> MagicMock:
    """Return a mocked MongoDB database."""
    return MagicMock()


@pytest.fixture
def jobs_collection() -> MagicMock:
    """Return a mocked jobs collection."""
    return MagicMock()


@pytest.fixture
def results_collection() -> MagicMock:
    """Return a mocked job results collection."""
    return MagicMock()


@pytest.fixture
def service(
    database: MagicMock,
    jobs_collection: MagicMock,
    results_collection: MagicMock,
) -> ProcessingService:
    """Create a processing service with mocked MongoDB collections."""
    database.__getitem__.side_effect = {
        "jobs": jobs_collection,
        "job_results": results_collection,
    }.get

    return ProcessingService(database)


@pytest.fixture
def valid_job() -> dict:
    """Return a valid background job."""
    return {
        "_id": "job-001",
        "status": "processing",
        "payload": {
            "operation": "generate_report",
            "report_id": "report-001",
        },
    }


def test_service_initializes_with_mongodb_collections(
    database: MagicMock,
    jobs_collection: MagicMock,
    results_collection: MagicMock,
) -> None:
    """The service resolves the configured MongoDB collections."""
    database.__getitem__.side_effect = {
        "jobs": jobs_collection,
        "job_results": results_collection,
    }.get

    service = ProcessingService(database)

    assert service._database is database
    assert service._jobs is jobs_collection
    assert service._results is results_collection


def test_process_valid_job(
    service: ProcessingService,
    valid_job: dict,
) -> None:
    """A valid job is processed successfully."""
    result = service.process(valid_job)

    assert result["status"] == "processed"
    assert result["payload"] == valid_job["payload"]
    assert isinstance(result["processed_at"], datetime)
    assert result["processed_at"].tzinfo == timezone.utc


def test_process_persists_result(
    service: ProcessingService,
    results_collection: MagicMock,
    valid_job: dict,
) -> None:
    """A successful job result is persisted using an upsert."""
    result = service.process(valid_job)

    results_collection.update_one.assert_called_once()

    filter_document, update_document = (
        results_collection.update_one.call_args.args
    )

    assert filter_document == {"job_id": "job-001"}
    assert update_document["$set"]["result"] == result
    assert isinstance(
        update_document["$set"]["updated_at"],
        datetime,
    )
    assert update_document["$setOnInsert"]["job_id"] == "job-001"
    assert isinstance(
        update_document["$setOnInsert"]["created_at"],
        datetime,
    )

    assert results_collection.update_one.call_args.kwargs == {
        "upsert": True,
    }


def test_process_is_idempotent_for_result_persistence(
    service: ProcessingService,
    results_collection: MagicMock,
    valid_job: dict,
) -> None:
    """Result persistence uses the job identifier as the upsert key."""
    service.process(valid_job)

    filter_document = (
        results_collection.update_one.call_args.args[0]
    )

    assert filter_document == {"job_id": valid_job["_id"]}


def test_process_rejects_empty_job(
    service: ProcessingService,
) -> None:
    """An empty job is rejected before processing."""
    with pytest.raises(
        InvalidJobError,
        match="Job must not be empty",
    ):
        service.process({})


def test_process_rejects_job_without_id(
    service: ProcessingService,
) -> None:
    """A job without an identifier is rejected."""
    job = {
        "payload": {
            "operation": "generate_report",
        },
    }

    with pytest.raises(
        InvalidJobError,
        match="Job must contain an _id",
    ):
        service.process(job)


def test_process_rejects_missing_payload(
    service: ProcessingService,
    valid_job: dict,
) -> None:
    """A job without a payload is rejected."""
    valid_job.pop("payload")

    with pytest.raises(
        InvalidJobError,
        match="Job payload must be a dictionary",
    ):
        service.process(valid_job)


@pytest.mark.parametrize(
    "payload",
    [
        None,
        "",
        [],
        (),
        "invalid",
        123,
    ],
)
def test_process_rejects_non_dictionary_payload(
    service: ProcessingService,
    valid_job: dict,
    payload: object,
) -> None:
    """A job payload must be a dictionary."""
    valid_job["payload"] = payload

    with pytest.raises(
        InvalidJobError,
        match="Job payload must be a dictionary",
    ):
        service.process(valid_job)


def test_validation_failure_does_not_persist_result(
    service: ProcessingService,
    results_collection: MagicMock,
) -> None:
    """Invalid jobs must not create result documents."""
    with pytest.raises(InvalidJobError):
        service.process(
            {
                "_id": "job-001",
                "payload": "invalid",
            }
        )

    results_collection.update_one.assert_not_called()


def test_processing_failure_is_wrapped(
    service: ProcessingService,
    valid_job: dict,
    results_collection: MagicMock,
) -> None:
    """Unexpected execution failures are wrapped in ProcessingError."""
    original_error = RuntimeError("processing failed")

    service._execute = MagicMock(side_effect=original_error)

    with pytest.raises(
        ProcessingError,
        match="Failed to process job 'job-001'",
    ) as exc_info:
        service.process(valid_job)

    assert exc_info.value.__cause__ is original_error
    results_collection.update_one.assert_not_called()


def test_mongodb_failure_is_wrapped(
    service: ProcessingService,
    valid_job: dict,
    results_collection: MagicMock,
) -> None:
    """MongoDB failures during persistence are exposed as processing errors."""
    mongodb_error = PyMongoError("MongoDB unavailable")
    results_collection.update_one.side_effect = mongodb_error

    with pytest.raises(
        ProcessingError,
        match="Failed to process job 'job-001'",
    ) as exc_info:
        service.process(valid_job)

    assert exc_info.value.__cause__ is mongodb_error


def test_processing_result_contains_original_payload(
    service: ProcessingService,
    valid_job: dict,
) -> None:
    """The processing result retains the submitted job payload."""
    result = service.process(valid_job)

    assert result["payload"] is valid_job["payload"]


def test_processing_timestamp_is_timezone_aware(
    service: ProcessingService,
    valid_job: dict,
) -> None:
    """Processing timestamps are stored as timezone-aware UTC values."""
    result = service.process(valid_job)

    processed_at = result["processed_at"]

    assert isinstance(processed_at, datetime)
    assert processed_at.tzinfo is not None
    assert processed_at.utcoffset() == timezone.utc.utcoffset(
        processed_at
    )


def test_processing_does_not_mutate_job(
    service: ProcessingService,
    valid_job: dict,
) -> None:
    """Processing does not modify the original job document."""
    original_job = {
        "_id": valid_job["_id"],
        "status": valid_job["status"],
        "payload": dict(valid_job["payload"]),
    }

    service.process(valid_job)

    assert valid_job == original_job


def test_process_calls_execution_once(
    service: ProcessingService,
    valid_job: dict,
) -> None:
    """Each successful process call executes the workload exactly once."""
    service._execute = MagicMock(
        return_value={
            "status": "processed",
            "payload": valid_job["payload"],
            "processed_at": datetime.now(timezone.utc),
        }
    )

    service.process(valid_job)

    service._execute.assert_called_once_with(
        valid_job["payload"]
    )


def test_process_does_not_persist_when_execution_fails(
    service: ProcessingService,
    valid_job: dict,
    results_collection: MagicMock,
) -> None:
    """A failed workload must not persist a successful result."""
    service._execute = MagicMock(
        side_effect=RuntimeError("execution failed")
    )

    with pytest.raises(ProcessingError):
        service.process(valid_job)

    results_collection.update_one.assert_not_called()

"""Tests for the MongoDB background job processing service."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from pymongo.errors import PyMongoError

from services.processing_service import (
    InvalidJobError,
    ProcessingError,
    ProcessingService,
)


@pytest.fixture
def database() -> MagicMock:
    """Return a mocked MongoDB database."""
    return MagicMock()


@pytest.fixture
def jobs_collection() -> MagicMock:
    """Return a mocked jobs collection."""
    return MagicMock()


@pytest.fixture
def results_collection() -> MagicMock:
    """Return a mocked job results collection."""
    return MagicMock()


@pytest.fixture
def service(
    database: MagicMock,
    jobs_collection: MagicMock,
    results_collection: MagicMock,
) -> ProcessingService:
    """Create a processing service with mocked MongoDB collections."""
    database.__getitem__.side_effect = {
        "jobs": jobs_collection,
        "job_results": results_collection,
    }.get

    return ProcessingService(database)


@pytest.fixture
def valid_job() -> dict:
    """Return a valid background job."""
    return {
        "_id": "job-001",
        "status": "processing",
        "payload": {
            "operation": "generate_report",
            "report_id": "report-001",
        },
    }


def test_service_initializes_with_mongodb_collections(
    database: MagicMock,
    jobs_collection: MagicMock,
    results_collection: MagicMock,
) -> None:
    """The service resolves the configured MongoDB collections."""
    database.__getitem__.side_effect = {
        "jobs": jobs_collection,
        "job_results": results_collection,
    }.get

    service = ProcessingService(database)

    assert service._database is database
    assert service._jobs is jobs_collection
    assert service._results is results_collection


def test_process_valid_job(
    service: ProcessingService,
    valid_job: dict,
) -> None:
    """A valid job is processed successfully."""
    result = service.process(valid_job)

    assert result["status"] == "processed"
    assert result["payload"] == valid_job["payload"]
    assert isinstance(result["processed_at"], datetime)
    assert result["processed_at"].tzinfo == timezone.utc


def test_process_persists_result(
    service: ProcessingService,
    results_collection: MagicMock,
    valid_job: dict,
) -> None:
    """A successful job result is persisted using an upsert."""
    result = service.process(valid_job)

    results_collection.update_one.assert_called_once()

    filter_document, update_document = (
        results_collection.update_one.call_args.args
    )

    assert filter_document == {"job_id": "job-001"}
    assert update_document["$set"]["result"] == result
    assert isinstance(
        update_document["$set"]["updated_at"],
        datetime,
    )
    assert update_document["$setOnInsert"]["job_id"] == "job-001"
    assert isinstance(
        update_document["$setOnInsert"]["created_at"],
        datetime,
    )

    assert results_collection.update_one.call_args.kwargs == {
        "upsert": True,
    }


def test_process_is_idempotent_for_result_persistence(
    service: ProcessingService,
    results_collection: MagicMock,
    valid_job: dict,
) -> None:
    """Result persistence uses the job identifier as the upsert key."""
    service.process(valid_job)

    filter_document = (
        results_collection.update_one.call_args.args[0]
    )

    assert filter_document == {"job_id": valid_job["_id"]}


def test_process_rejects_empty_job(
    service: ProcessingService,
) -> None:
    """An empty job is rejected before processing."""
    with pytest.raises(
        InvalidJobError,
        match="Job must not be empty",
    ):
        service.process({})


def test_process_rejects_job_without_id(
    service: ProcessingService,
) -> None:
    """A job without an identifier is rejected."""
    job = {
        "payload": {
            "operation": "generate_report",
        },
    }

    with pytest.raises(
        InvalidJobError,
        match="Job must contain an _id",
    ):
        service.process(job)


def test_process_rejects_missing_payload(
    service: ProcessingService,
    valid_job: dict,
) -> None:
    """A job without a payload is rejected."""
    valid_job.pop("payload")

    with pytest.raises(
        InvalidJobError,
        match="Job payload must be a dictionary",
    ):
        service.process(valid_job)


@pytest.mark.parametrize(
    "payload",
    [
        None,
        "",
        [],
        (),
        "invalid",
        123,
    ],
)
def test_process_rejects_non_dictionary_payload(
    service: ProcessingService,
    valid_job: dict,
    payload: object,
) -> None:
    """A job payload must be a dictionary."""
    valid_job["payload"] = payload

    with pytest.raises(
        InvalidJobError,
        match="Job payload must be a dictionary",
    ):
        service.process(valid_job)


def test_validation_failure_does_not_persist_result(
    service: ProcessingService,
    results_collection: MagicMock,
) -> None:
    """Invalid jobs must not create result documents."""
    with pytest.raises(InvalidJobError):
        service.process(
            {
                "_id": "job-001",
                "payload": "invalid",
            }
        )

    results_collection.update_one.assert_not_called()


def test_processing_failure_is_wrapped(
    service: ProcessingService,
    valid_job: dict,
    results_collection: MagicMock,
) -> None:
    """Unexpected execution failures are wrapped in ProcessingError."""
    original_error = RuntimeError("processing failed")

    service._execute = MagicMock(side_effect=original_error)

    with pytest.raises(
        ProcessingError,
        match="Failed to process job 'job-001'",
    ) as exc_info:
        service.process(valid_job)

    assert exc_info.value.__cause__ is original_error
    results_collection.update_one.assert_not_called()


def test_mongodb_failure_is_wrapped(
    service: ProcessingService,
    valid_job: dict,
    results_collection: MagicMock,
) -> None:
    """MongoDB failures during persistence are exposed as processing errors."""
    mongodb_error = PyMongoError("MongoDB unavailable")
    results_collection.update_one.side_effect = mongodb_error

    with pytest.raises(
        ProcessingError,
        match="Failed to process job 'job-001'",
    ) as exc_info:
        service.process(valid_job)

    assert exc_info.value.__cause__ is mongodb_error


def test_processing_result_contains_original_payload(
    service: ProcessingService,
    valid_job: dict,
) -> None:
    """The processing result retains the submitted job payload."""
    result = service.process(valid_job)

    assert result["payload"] is valid_job["payload"]


def test_processing_timestamp_is_timezone_aware(
    service: ProcessingService,
    valid_job: dict,
) -> None:
    """Processing timestamps are stored as timezone-aware UTC values."""
    result = service.process(valid_job)

    processed_at = result["processed_at"]

    assert isinstance(processed_at, datetime)
    assert processed_at.tzinfo is not None
    assert processed_at.utcoffset() == timezone.utc.utcoffset(
        processed_at
    )


def test_processing_does_not_mutate_job(
    service: ProcessingService,
    valid_job: dict,
) -> None:
    """Processing does not modify the original job document."""
    original_job = {
        "_id": valid_job["_id"],
        "status": valid_job["status"],
        "payload": dict(valid_job["payload"]),
    }

    service.process(valid_job)

    assert valid_job == original_job


def test_process_calls_execution_once(
    service: ProcessingService,
    valid_job: dict,
) -> None:
    """Each successful process call executes the workload exactly once."""
    service._execute = MagicMock(
        return_value={
            "status": "processed",
            "payload": valid_job["payload"],
            "processed_at": datetime.now(timezone.utc),
        }
    )

    service.process(valid_job)

    service._execute.assert_called_once_with(
        valid_job["payload"]
    )


def test_process_does_not_persist_when_execution_fails(
    service: ProcessingService,
    valid_job: dict,
    results_collection: MagicMock,
) -> None:
    """A failed workload must not persist a successful result."""
    service._execute = MagicMock(
        side_effect=RuntimeError("execution failed")
    )

    with pytest.raises(ProcessingError):
        service.process(valid_job)

    results_collection.update_one.assert_not_called()