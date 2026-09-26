"""Application service for processing MongoDB background jobs."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database

from config.settings import (
    MONGODB_JOBS_COLLECTION,
    MONGODB_RESULTS_COLLECTION,
)

logger = logging.getLogger(__name__)


class ProcessingError(Exception):
    """Base exception for background job processing failures."""


class InvalidJobError(ProcessingError):
    """Raised when a background job contains invalid input."""


class ProcessingService:
    """Coordinate validation, execution, and persistence of background jobs."""

    def __init__(self, database: Database) -> None:
        self._database = database
        self._jobs: Collection = database[MONGODB_JOBS_COLLECTION]
        self._results: Collection = database[MONGODB_RESULTS_COLLECTION]

    def process(self, job: dict[str, Any]) -> dict[str, Any]:
        """Process a job and persist its result."""
        job_id = job.get("_id")

        try:
            payload = self._validate_job(job)
            result = self._execute(payload)
            self._persist_result(job_id, result)
            return result
        except ProcessingError:
            raise
        except Exception as exc:
            logger.exception("Unexpected error processing job %s", job_id)
            raise ProcessingError(
                f"Failed to process job {job_id!r}"
            ) from exc

    def _validate_job(self, job: dict[str, Any]) -> dict[str, Any]:
        """Validate and return the job payload."""
        if not job:
            raise InvalidJobError("Job must not be empty")

        if "_id" not in job:
            raise InvalidJobError("Job must contain an _id")

        payload = job.get("payload")

        if not isinstance(payload, dict):
            raise InvalidJobError("Job payload must be a dictionary")

        return payload

    def _execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute the application-specific processing workload."""
        return {
            "status": "processed",
            "payload": payload,
            "processed_at": datetime.now(timezone.utc),
        }

    def _persist_result(
        self,
        job_id: Any,
        result: dict[str, Any],
    ) -> None:
        """Persist a processed job result in MongoDB."""
        self._results.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "result": result,
                    "updated_at": datetime.now(timezone.utc),
                },
                "$setOnInsert": {
                    "job_id": job_id,
                    "created_at": datetime.now(timezone.utc),
                },
            },
            upsert=True,
        )

"""Application service for processing MongoDB background jobs."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database

from config.settings import (
    MONGODB_JOBS_COLLECTION,
    MONGODB_RESULTS_COLLECTION,
)

logger = logging.getLogger(__name__)


class ProcessingError(Exception):
    """Base exception for background job processing failures."""


class InvalidJobError(ProcessingError):
    """Raised when a background job contains invalid input."""


class ProcessingService:
    """Coordinate validation, execution, and persistence of background jobs."""

    def __init__(self, database: Database) -> None:
        self._database = database
        self._jobs: Collection = database[MONGODB_JOBS_COLLECTION]
        self._results: Collection = database[MONGODB_RESULTS_COLLECTION]

    def process(self, job: dict[str, Any]) -> dict[str, Any]:
        """Process a job and persist its result."""
        job_id = job.get("_id")

        try:
            payload = self._validate_job(job)
            result = self._execute(payload)
            self._persist_result(job_id, result)
            return result
        except ProcessingError:
            raise
        except Exception as exc:
            logger.exception("Unexpected error processing job %s", job_id)
            raise ProcessingError(
                f"Failed to process job {job_id!r}"
            ) from exc

    def _validate_job(self, job: dict[str, Any]) -> dict[str, Any]:
        """Validate and return the job payload."""
        if not job:
            raise InvalidJobError("Job must not be empty")

        if "_id" not in job:
            raise InvalidJobError("Job must contain an _id")

        payload = job.get("payload")

        if not isinstance(payload, dict):
            raise InvalidJobError("Job payload must be a dictionary")

        return payload

    def _execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute the application-specific processing workload."""
        return {
            "status": "processed",
            "payload": payload,
            "processed_at": datetime.now(timezone.utc),
        }

    def _persist_result(
        self,
        job_id: Any,
        result: dict[str, Any],
    ) -> None:
        """Persist a processed job result in MongoDB."""
        self._results.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "result": result,
                    "updated_at": datetime.now(timezone.utc),
                },
                "$setOnInsert": {
                    "job_id": job_id,
                    "created_at": datetime.now(timezone.utc),
                },
            },
            upsert=True,
        )