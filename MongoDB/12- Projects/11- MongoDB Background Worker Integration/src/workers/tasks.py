"""Background worker tasks for MongoDB job processing."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database

from config.settings import (
    MONGODB_JOBS_COLLECTION,
    MONGODB_RESULTS_COLLECTION,
    WORKER_MAX_RETRIES,
    WORKER_RETRY_DELAY_SECONDS,
)

logger = logging.getLogger(__name__)

STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def get_jobs_collection(database: Database) -> Collection:
    """Return the MongoDB collection containing background jobs."""
    return database[MONGODB_JOBS_COLLECTION]


def get_results_collection(database: Database) -> Collection:
    """Return the MongoDB collection containing job results."""
    return database[MONGODB_RESULTS_COLLECTION]


def claim_job(
    database: Database,
    worker_name: str,
) -> dict[str, Any] | None:
    """Atomically claim the next pending job for a worker."""
    jobs = get_jobs_collection(database)

    result = jobs.find_one_and_update(
        {"status": STATUS_PENDING},
        {
            "$set": {
                "status": STATUS_PROCESSING,
                "worker_name": worker_name,
                "started_at": utc_now(),
            },
            "$inc": {"attempts": 1},
        },
        sort=[("created_at", 1)],
        return_document=True,
    )

    return result


def process_job(
    database: Database,
    job: dict[str, Any],
) -> dict[str, Any]:
    """Process a claimed job and persist its result."""
    jobs = get_jobs_collection(database)
    results = get_results_collection(database)

    job_id = job["_id"]
    payload = job.get("payload", {})

    try:
        result = execute_job(payload)

        results.insert_one(
            {
                "job_id": job_id,
                "result": result,
                "created_at": utc_now(),
            }
        )

        jobs.update_one(
            {"_id": job_id, "status": STATUS_PROCESSING},
            {
                "$set": {
                    "status": STATUS_COMPLETED,
                    "completed_at": utc_now(),
                },
                "$unset": {
                    "worker_name": "",
                },
            },
        )

        return result

    except Exception as exc:
        logger.exception("Failed to process job %s", job_id)
        handle_job_failure(database, job, exc)
        raise


def execute_job(payload: dict[str, Any]) -> dict[str, Any]:
    """Execute the application-specific background workload."""
    return {
        "status": "processed",
        "payload": payload,
        "processed_at": utc_now(),
    }


def handle_job_failure(
    database: Database,
    job: dict[str, Any],
    error: Exception,
) -> None:
    """Record a failed attempt and determine whether the job can retry."""
    jobs = get_jobs_collection(database)

    attempts = int(job.get("attempts", 0))
    job_id = job["_id"]

    if attempts < WORKER_MAX_RETRIES:
        time.sleep(WORKER_RETRY_DELAY_SECONDS)

        jobs.update_one(
            {"_id": job_id, "status": STATUS_PROCESSING},
            {
                "$set": {
                    "status": STATUS_PENDING,
                    "last_error": str(error),
                    "retry_at": utc_now(),
                },
                "$unset": {
                    "worker_name": "",
                    "started_at": "",
                },
            },
        )
        return

    jobs.update_one(
        {"_id": job_id, "status": STATUS_PROCESSING},
        {
            "$set": {
                "status": STATUS_FAILED,
                "last_error": str(error),
                "failed_at": utc_now(),
            },
            "$unset": {
                "worker_name": "",
            },
        },
    )


def run_worker(
    database: Database,
    worker_name: str,
    poll_interval_seconds: int,
) -> None:
    """Continuously claim and process pending jobs."""
    logger.info("Starting MongoDB worker: %s", worker_name)

    while True:
        job = claim_job(database, worker_name)

        if job is None:
            time.sleep(poll_interval_seconds)
            continue

        try:
            process_job(database, job)
        except Exception:
            logger.exception(
                "Worker failed while processing job %s",
                job.get("_id"),
            )

"""Background worker tasks for MongoDB job processing."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database

from config.settings import (
    MONGODB_JOBS_COLLECTION,
    MONGODB_RESULTS_COLLECTION,
    WORKER_MAX_RETRIES,
    WORKER_RETRY_DELAY_SECONDS,
)

logger = logging.getLogger(__name__)

STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def get_jobs_collection(database: Database) -> Collection:
    """Return the MongoDB collection containing background jobs."""
    return database[MONGODB_JOBS_COLLECTION]


def get_results_collection(database: Database) -> Collection:
    """Return the MongoDB collection containing job results."""
    return database[MONGODB_RESULTS_COLLECTION]


def claim_job(
    database: Database,
    worker_name: str,
) -> dict[str, Any] | None:
    """Atomically claim the next pending job for a worker."""
    jobs = get_jobs_collection(database)

    result = jobs.find_one_and_update(
        {"status": STATUS_PENDING},
        {
            "$set": {
                "status": STATUS_PROCESSING,
                "worker_name": worker_name,
                "started_at": utc_now(),
            },
            "$inc": {"attempts": 1},
        },
        sort=[("created_at", 1)],
        return_document=True,
    )

    return result


def process_job(
    database: Database,
    job: dict[str, Any],
) -> dict[str, Any]:
    """Process a claimed job and persist its result."""
    jobs = get_jobs_collection(database)
    results = get_results_collection(database)

    job_id = job["_id"]
    payload = job.get("payload", {})

    try:
        result = execute_job(payload)

        results.insert_one(
            {
                "job_id": job_id,
                "result": result,
                "created_at": utc_now(),
            }
        )

        jobs.update_one(
            {"_id": job_id, "status": STATUS_PROCESSING},
            {
                "$set": {
                    "status": STATUS_COMPLETED,
                    "completed_at": utc_now(),
                },
                "$unset": {
                    "worker_name": "",
                },
            },
        )

        return result

    except Exception as exc:
        logger.exception("Failed to process job %s", job_id)
        handle_job_failure(database, job, exc)
        raise


def execute_job(payload: dict[str, Any]) -> dict[str, Any]:
    """Execute the application-specific background workload."""
    return {
        "status": "processed",
        "payload": payload,
        "processed_at": utc_now(),
    }


def handle_job_failure(
    database: Database,
    job: dict[str, Any],
    error: Exception,
) -> None:
    """Record a failed attempt and determine whether the job can retry."""
    jobs = get_jobs_collection(database)

    attempts = int(job.get("attempts", 0))
    job_id = job["_id"]

    if attempts < WORKER_MAX_RETRIES:
        time.sleep(WORKER_RETRY_DELAY_SECONDS)

        jobs.update_one(
            {"_id": job_id, "status": STATUS_PROCESSING},
            {
                "$set": {
                    "status": STATUS_PENDING,
                    "last_error": str(error),
                    "retry_at": utc_now(),
                },
                "$unset": {
                    "worker_name": "",
                    "started_at": "",
                },
            },
        )
        return

    jobs.update_one(
        {"_id": job_id, "status": STATUS_PROCESSING},
        {
            "$set": {
                "status": STATUS_FAILED,
                "last_error": str(error),
                "failed_at": utc_now(),
            },
            "$unset": {
                "worker_name": "",
            },
        },
    )


def run_worker(
    database: Database,
    worker_name: str,
    poll_interval_seconds: int,
) -> None:
    """Continuously claim and process pending jobs."""
    logger.info("Starting MongoDB worker: %s", worker_name)

    while True:
        job = claim_job(database, worker_name)

        if job is None:
            time.sleep(poll_interval_seconds)
            continue

        try:
            process_job(database, job)
        except Exception:
            logger.exception(
                "Worker failed while processing job %s",
                job.get("_id"),
            )