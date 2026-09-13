"""Run the asynchronous API client."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.client import AsyncAPIClient
from src.config import ClientConfig
from src.exceptions import APIClientError
from src.rate_limiter import AsyncRateLimiter


logger = logging.getLogger(__name__)


async def run() -> None:
    """Execute the client workflow against the configured API."""
    config = ClientConfig.from_environment()
    rate_limiter = AsyncRateLimiter(config.rate_limit_per_second)

    async with AsyncAPIClient(config) as client:
        async with rate_limiter:
            response = await client.get("/users")

        logger.info("Received response from API: %s", response)


def main() -> int:
    """Configure logging and run the asynchronous client."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Client execution interrupted.")
        return 130
    except APIClientError:
        logger.exception("API client execution failed.")
        return 1
    except ValueError:
        logger.exception("Invalid client configuration.")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Run the asynchronous API client."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.client import AsyncAPIClient
from src.config import ClientConfig
from src.exceptions import APIClientError
from src.rate_limiter import AsyncRateLimiter


logger = logging.getLogger(__name__)


async def run() -> None:
    """Execute the client workflow against the configured API."""
    config = ClientConfig.from_environment()
    rate_limiter = AsyncRateLimiter(config.rate_limit_per_second)

    async with AsyncAPIClient(config) as client:
        async with rate_limiter:
            response = await client.get("/users")

        logger.info("Received response from API: %s", response)


def main() -> int:
    """Configure logging and run the asynchronous client."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Client execution interrupted.")
        return 130
    except APIClientError:
        logger.exception("API client execution failed.")
        return 1
    except ValueError:
        logger.exception("Invalid client configuration.")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())