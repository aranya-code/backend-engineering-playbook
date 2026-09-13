"""Application entry point for the asynchronous API client."""

from __future__ import annotations

import asyncio
import logging

from src.client import AsyncAPIClient
from src.config import ClientConfig
from src.rate_limiter import AsyncRateLimiter

logger = logging.getLogger(__name__)


async def run() -> None:
    """Run a small production-style client workflow."""
    config = ClientConfig.from_environment()
    rate_limiter = AsyncRateLimiter(config.rate_limit_per_second)

    async with AsyncAPIClient(config) as client:
        async with rate_limiter:
            response = await client.get("/users")

        logger.info("Received response from API: %s", response)


def main() -> None:
    """Start the asynchronous client application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    asyncio.run(run())


if __name__ == "__main__":
    main()

"""Application entry point for the asynchronous API client."""

from __future__ import annotations

import asyncio
import logging

from src.client import AsyncAPIClient
from src.config import ClientConfig
from src.rate_limiter import AsyncRateLimiter

logger = logging.getLogger(__name__)


async def run() -> None:
    """Run a small production-style client workflow."""
    config = ClientConfig.from_environment()
    rate_limiter = AsyncRateLimiter(config.rate_limit_per_second)

    async with AsyncAPIClient(config) as client:
        async with rate_limiter:
            response = await client.get("/users")

        logger.info("Received response from API: %s", response)


def main() -> None:
    """Start the asynchronous client application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    asyncio.run(run())


if __name__ == "__main__":
    main()