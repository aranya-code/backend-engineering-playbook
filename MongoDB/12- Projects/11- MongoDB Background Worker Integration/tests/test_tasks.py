"""Tests for MongoDB background worker tasks."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from pymongo import ReturnDocument

from workers.tasks import (
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_PROCESSING,
    claim_job,
    execute_job,
    handle_job_failure,
    process_job,
    run_worker,
)


@pytest.fixture
def database() -> MagicMock:
    """Return a mocked MongoDB database."""
    return MagicMock()


@pytest.fixture
def jobs_collection(database: MagicMock) -> MagicMock:
    """Return the mocked jobs collection."""
    collection = MagicMock()
    database.__getitem__.side_effect = {
        "jobs": collection,
    }.get
    return collection


def test_execute_job_returns_processed_result() -> None:
    """Job execution returns a processed result with UTC timestamp."""
    payload = {"operation": "generate_report", "report_id": "report-001"}

    result = execute_job(payload)

    assert result["status"] == "processed"
    assert result["payload"] == payload
    assert isinstance(result["processed_at"], datetime)
    assert result["processed_at"].tzinfo == timezone.utc


def test_claim_job_atomically_claims_pending_job(
    database: MagicMock,
    jobs_collection: MagicMock,
) -> None:
    """A pending job is claimed with an atomic MongoDB update."""
    job = {
        "_id": "job-001",
        "status": STATUS_PROCESSING,
        "attempts": 1,
    }
    jobs_collection.find_one_and_update.return_value = job

    result = claim_job(database, "worker-001")

    assert result == job
    jobs_collection.find_one_and_update.assert_called_once()

    filter_document, update_document = (
        jobs_collection.find_one_and_update.call_args.args
    )

    assert filter_document == {"status": STATUS_PENDING}
    assert update_document["$set"]["status"] == STATUS_PROCESSING
    assert update_document["$set"]["worker_name"] == "worker-001"
    assert "started_at" in update_document["$set"]
    assert update_document["$inc"] == {"attempts": 1}

    kwargs = jobs_collection.find_one_and_update.call_args.kwargs
    assert kwargs["sort"] == [("created_at", 1)]
    assert kwargs["return_document"] is True


def test_claim_job_returns_none_when_no_pending_job(
    database: MagicMock,
    jobs_collection: MagicMock,
) -> None:
    """No job is returned when the queue has no pending work."""
    jobs_collection.find_one_and_update.return_value = None

    assert claim_job(database, "worker-001") is None


def test_process_job_persists_result_and_completes_job(
    database: MagicMock,
) -> None:
    """Successful processing stores the result and marks the job completed."""
    jobs_collection = MagicMock()
    results_collection = MagicMock()

    database.__getitem__.side_effect = {
        "jobs": jobs_collection,
        "job_results": results_collection,
    }.get

    job = {
        "_id": "job-001",
        "status": STATUS_PROCESSING,
        "payload": {"operation": "generate_report"},
    }

    result = process_job(database, job)

    assert result["status"] == "processed"
    results_collection.update_one.assert_called_once()

    result_filter, result_update = (
        results_collection.update_one.call_args.args
    )

    assert result_filter == {"job_id": "job-001"}
    assert result_update["$set"]["result"] == result
    assert "updated_at" in result_update["$set"]
    assert result_update["$setOnInsert"]["job_id"] == "job-001"
    assert "created_at" in result_update["$setOnInsert"]

    jobs_collection.update_one.assert_called_once()

    job_filter, job_update = jobs_collection.update_one.call_args.args

    assert job_filter == {
        "_id": "job-001",
        "status": STATUS_PROCESSING,
    }
    assert job_update["$set"]["status"] == STATUS_COMPLETED
    assert "completed_at" in job_update["$set"]


def test_process_job_rejects_missing_payload(
    database: MagicMock,
) -> None:
    """Jobs without a dictionary payload are rejected."""
    job = {
        "_id": "job-001",
        "status": STATUS_PROCESSING,
    }

    with pytest.raises(ValueError):
        process_job(database, job)


def test_process_job_rejects_missing_job_id(
    database: MagicMock,
) -> None:
    """Jobs without an identifier are rejected."""
    job = {
        "status": STATUS_PROCESSING,
        "payload": {},
    }

    with pytest.raises(ValueError):
        process_job(database, job)


def test_process_job_handles_execution_failure(
    database: MagicMock,
) -> None:
    """Processing failures are recorded and propagated."""
    jobs_collection = MagicMock()
    results_collection = MagicMock()

    database.__getitem__.side_effect = {
        "jobs": jobs_collection,
        "job_results": results_collection,
    }.get

    job = {
        "_id": "job-001",
        "status": STATUS_PROCESSING,
        "attempts": 1,
        "payload": {"operation": "generate_report"},
    }

    with patch(
        "workers.tasks.execute_job",
        side_effect=RuntimeError("processing failed"),
    ):
        with patch(
            "workers.tasks.WORKER_RETRY_DELAY_SECONDS",
            0,
        ):
            with pytest.raises(RuntimeError, match="processing failed"):
                process_job(database, job)

    jobs_collection.update_one.assert_called_once()

    _, update_document = jobs_collection.update_one.call_args.args

    assert update_document["$set"]["status"] == STATUS_PENDING
    assert update_document["$set"]["last_error"] == "processing failed"


def test_handle_job_failure_requeues_retryable_job(
    database: MagicMock,
) -> None:
    """A job below the retry limit is returned to the pending queue."""
    jobs_collection = MagicMock()
    database.__getitem__.side_effect = {
        "jobs": jobs_collection,
    }.get

    job = {
        "_id": "job-001",
        "attempts": 1,
        "status": STATUS_PROCESSING,
    }

    with patch(
        "workers.tasks.WORKER_MAX_RETRIES",
        3,
    ):
        with patch(
            "workers.tasks.WORKER_RETRY_DELAY_SECONDS",
            0,
        ):
            handle_job_failure(
                database,
                job,
                RuntimeError("temporary failure"),
            )

    jobs_collection.update_one.assert_called_once()

    filter_document, update_document = (
        jobs_collection.update_one.call_args.args
    )

    assert filter_document == {
        "_id": "job-001",
        "status": STATUS_PROCESSING,
    }
    assert update_document["$set"]["status"] == STATUS_PENDING
    assert update_document["$set"]["last_error"] == "temporary failure"
    assert "retry_at" in update_document["$set"]


def test_handle_job_failure_marks_job_failed_after_retry_limit(
    database: MagicMock,
) -> None:
    """A job at the retry limit is permanently marked as failed."""
    jobs_collection = MagicMock()
    database.__getitem__.side_effect = {
        "jobs": jobs_collection,
    }.get

    job = {
        "_id": "job-001",
        "attempts": 3,
        "status": STATUS_PROCESSING,
    }

    with patch(
        "workers.tasks.WORKER_MAX_RETRIES",
        3,
    ):
        handle_job_failure(
            database,
            job,
            RuntimeError("permanent failure"),
        )

    jobs_collection.update_one.assert_called_once()

    _, update_document = jobs_collection.update_one.call_args.args

    assert update_document["$set"]["status"] == STATUS_FAILED
    assert update_document["$set"]["last_error"] == "permanent failure"
    assert "failed_at" in update_document["$set"]


def test_run_worker_processes_claimed_job_once(
    database: MagicMock,
) -> None:
    """A claimed job is passed to the processing function."""
    job = {
        "_id": "job-001",
        "status": STATUS_PROCESSING,
        "payload": {},
    }

    with patch(
        "workers.tasks.claim_job",
        side_effect=[job, KeyboardInterrupt],
    ) as mock_claim:
        with patch(
            "workers.tasks.process_job",
        ) as mock_process:
            with pytest.raises(KeyboardInterrupt):
                run_worker(
                    database,
                    "worker-001",
                    1,
                )

    mock_claim.assert_called_once_with(database, "worker-001")
    mock_process.assert_called_once_with(database, job)


def test_run_worker_polls_when_queue_is_empty(
    database: MagicMock,
) -> None:
    """The worker waits before polling again when no job is available."""
    with patch(
        "workers.tasks.claim_job",
        side_effect=[None, KeyboardInterrupt],
    ) as mock_claim:
        with patch("workers.tasks.time.sleep") as mock_sleep:
            with pytest.raises(KeyboardInterrupt):
                run_worker(
                    database,
                    "worker-001",
                    5,
                )

    mock_claim.assert_called_once_with(database, "worker-001")
    mock_sleep.assert_called_once_with(5)


def test_run_worker_continues_after_processing_failure(
    database: MagicMock,
) -> None:
    """A processing failure does not terminate the worker loop."""
    job = {
        "_id": "job-001",
        "status": STATUS_PROCESSING,
        "payload": {},
    }

    with patch(
        "workers.tasks.claim_job",
        side_effect=[job, KeyboardInterrupt],
    ):
        with patch(
            "workers.tasks.process_job",
            side_effect=RuntimeError("processing failed"),
        ) as mock_process:
            with pytest.raises(KeyboardInterrupt):
                run_worker(
                    database,
                    "worker-001",
                    1,
                )

    mock_process.assert_called_once_with(database, job)

"""Tests for MongoDB background worker tasks."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from pymongo import ReturnDocument

from workers.tasks import (
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_PROCESSING,
    claim_job,
    execute_job,
    handle_job_failure,
    process_job,
    run_worker,
)


@pytest.fixture
def database() -> MagicMock:
    """Return a mocked MongoDB database."""
    return MagicMock()


@pytest.fixture
def jobs_collection(database: MagicMock) -> MagicMock:
    """Return the mocked jobs collection."""
    collection = MagicMock()
    database.__getitem__.side_effect = {
        "jobs": collection,
    }.get
    return collection


def test_execute_job_returns_processed_result() -> None:
    """Job execution returns a processed result with UTC timestamp."""
    payload = {"operation": "generate_report", "report_id": "report-001"}

    result = execute_job(payload)

    assert result["status"] == "processed"
    assert result["payload"] == payload
    assert isinstance(result["processed_at"], datetime)
    assert result["processed_at"].tzinfo == timezone.utc


def test_claim_job_atomically_claims_pending_job(
    database: MagicMock,
    jobs_collection: MagicMock,
) -> None:
    """A pending job is claimed with an atomic MongoDB update."""
    job = {
        "_id": "job-001",
        "status": STATUS_PROCESSING,
        "attempts": 1,
    }
    jobs_collection.find_one_and_update.return_value = job

    result = claim_job(database, "worker-001")

    assert result == job
    jobs_collection.find_one_and_update.assert_called_once()

    filter_document, update_document = (
        jobs_collection.find_one_and_update.call_args.args
    )

    assert filter_document == {"status": STATUS_PENDING}
    assert update_document["$set"]["status"] == STATUS_PROCESSING
    assert update_document["$set"]["worker_name"] == "worker-001"
    assert "started_at" in update_document["$set"]
    assert update_document["$inc"] == {"attempts": 1}

    kwargs = jobs_collection.find_one_and_update.call_args.kwargs
    assert kwargs["sort"] == [("created_at", 1)]
    assert kwargs["return_document"] is True


def test_claim_job_returns_none_when_no_pending_job(
    database: MagicMock,
    jobs_collection: MagicMock,
) -> None:
    """No job is returned when the queue has no pending work."""
    jobs_collection.find_one_and_update.return_value = None

    assert claim_job(database, "worker-001") is None


def test_process_job_persists_result_and_completes_job(
    database: MagicMock,
) -> None:
    """Successful processing stores the result and marks the job completed."""
    jobs_collection = MagicMock()
    results_collection = MagicMock()

    database.__getitem__.side_effect = {
        "jobs": jobs_collection,
        "job_results": results_collection,
    }.get

    job = {
        "_id": "job-001",
        "status": STATUS_PROCESSING,
        "payload": {"operation": "generate_report"},
    }

    result = process_job(database, job)

    assert result["status"] == "processed"
    results_collection.update_one.assert_called_once()

    result_filter, result_update = (
        results_collection.update_one.call_args.args
    )

    assert result_filter == {"job_id": "job-001"}
    assert result_update["$set"]["result"] == result
    assert "updated_at" in result_update["$set"]
    assert result_update["$setOnInsert"]["job_id"] == "job-001"
    assert "created_at" in result_update["$setOnInsert"]

    jobs_collection.update_one.assert_called_once()

    job_filter, job_update = jobs_collection.update_one.call_args.args

    assert job_filter == {
        "_id": "job-001",
        "status": STATUS_PROCESSING,
    }
    assert job_update["$set"]["status"] == STATUS_COMPLETED
    assert "completed_at" in job_update["$set"]


def test_process_job_rejects_missing_payload(
    database: MagicMock,
) -> None:
    """Jobs without a dictionary payload are rejected."""
    job = {
        "_id": "job-001",
        "status": STATUS_PROCESSING,
    }

    with pytest.raises(ValueError):
        process_job(database, job)


def test_process_job_rejects_missing_job_id(
    database: MagicMock,
) -> None:
    """Jobs without an identifier are rejected."""
    job = {
        "status": STATUS_PROCESSING,
        "payload": {},
    }

    with pytest.raises(ValueError):
        process_job(database, job)


def test_process_job_handles_execution_failure(
    database: MagicMock,
) -> None:
    """Processing failures are recorded and propagated."""
    jobs_collection = MagicMock()
    results_collection = MagicMock()

    database.__getitem__.side_effect = {
        "jobs": jobs_collection,
        "job_results": results_collection,
    }.get

    job = {
        "_id": "job-001",
        "status": STATUS_PROCESSING,
        "attempts": 1,
        "payload": {"operation": "generate_report"},
    }

    with patch(
        "workers.tasks.execute_job",
        side_effect=RuntimeError("processing failed"),
    ):
        with patch(
            "workers.tasks.WORKER_RETRY_DELAY_SECONDS",
            0,
        ):
            with pytest.raises(RuntimeError, match="processing failed"):
                process_job(database, job)

    jobs_collection.update_one.assert_called_once()

    _, update_document = jobs_collection.update_one.call_args.args

    assert update_document["$set"]["status"] == STATUS_PENDING
    assert update_document["$set"]["last_error"] == "processing failed"


def test_handle_job_failure_requeues_retryable_job(
    database: MagicMock,
) -> None:
    """A job below the retry limit is returned to the pending queue."""
    jobs_collection = MagicMock()
    database.__getitem__.side_effect = {
        "jobs": jobs_collection,
    }.get

    job = {
        "_id": "job-001",
        "attempts": 1,
        "status": STATUS_PROCESSING,
    }

    with patch(
        "workers.tasks.WORKER_MAX_RETRIES",
        3,
    ):
        with patch(
            "workers.tasks.WORKER_RETRY_DELAY_SECONDS",
            0,
        ):
            handle_job_failure(
                database,
                job,
                RuntimeError("temporary failure"),
            )

    jobs_collection.update_one.assert_called_once()

    filter_document, update_document = (
        jobs_collection.update_one.call_args.args
    )

    assert filter_document == {
        "_id": "job-001",
        "status": STATUS_PROCESSING,
    }
    assert update_document["$set"]["status"] == STATUS_PENDING
    assert update_document["$set"]["last_error"] == "temporary failure"
    assert "retry_at" in update_document["$set"]


def test_handle_job_failure_marks_job_failed_after_retry_limit(
    database: MagicMock,
) -> None:
    """A job at the retry limit is permanently marked as failed."""
    jobs_collection = MagicMock()
    database.__getitem__.side_effect = {
        "jobs": jobs_collection,
    }.get

    job = {
        "_id": "job-001",
        "attempts": 3,
        "status": STATUS_PROCESSING,
    }

    with patch(
        "workers.tasks.WORKER_MAX_RETRIES",
        3,
    ):
        handle_job_failure(
            database,
            job,
            RuntimeError("permanent failure"),
        )

    jobs_collection.update_one.assert_called_once()

    _, update_document = jobs_collection.update_one.call_args.args

    assert update_document["$set"]["status"] == STATUS_FAILED
    assert update_document["$set"]["last_error"] == "permanent failure"
    assert "failed_at" in update_document["$set"]


def test_run_worker_processes_claimed_job_once(
    database: MagicMock,
) -> None:
    """A claimed job is passed to the processing function."""
    job = {
        "_id": "job-001",
        "status": STATUS_PROCESSING,
        "payload": {},
    }

    with patch(
        "workers.tasks.claim_job",
        side_effect=[job, KeyboardInterrupt],
    ) as mock_claim:
        with patch(
            "workers.tasks.process_job",
        ) as mock_process:
            with pytest.raises(KeyboardInterrupt):
                run_worker(
                    database,
                    "worker-001",
                    1,
                )

    mock_claim.assert_called_once_with(database, "worker-001")
    mock_process.assert_called_once_with(database, job)


def test_run_worker_polls_when_queue_is_empty(
    database: MagicMock,
) -> None:
    """The worker waits before polling again when no job is available."""
    with patch(
        "workers.tasks.claim_job",
        side_effect=[None, KeyboardInterrupt],
    ) as mock_claim:
        with patch("workers.tasks.time.sleep") as mock_sleep:
            with pytest.raises(KeyboardInterrupt):
                run_worker(
                    database,
                    "worker-001",
                    5,
                )

    mock_claim.assert_called_once_with(database, "worker-001")
    mock_sleep.assert_called_once_with(5)


def test_run_worker_continues_after_processing_failure(
    database: MagicMock,
) -> None:
    """A processing failure does not terminate the worker loop."""
    job = {
        "_id": "job-001",
        "status": STATUS_PROCESSING,
        "payload": {},
    }

    with patch(
        "workers.tasks.claim_job",
        side_effect=[job, KeyboardInterrupt],
    ):
        with patch(
            "workers.tasks.process_job",
            side_effect=RuntimeError("processing failed"),
        ) as mock_process:
            with pytest.raises(KeyboardInterrupt):
                run_worker(
                    database,
                    "worker-001",
                    1,
                )

    mock_process.assert_called_once_with(database, job)