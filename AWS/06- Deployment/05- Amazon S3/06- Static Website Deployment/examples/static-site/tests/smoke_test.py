"""Smoke tests for the deployed S3-backed static website.

The tests validate the public CloudFront or custom-domain endpoint after
deployment. They do not require AWS credentials because requests are made
through the website's HTTPS endpoint.

Usage:
    python -m pytest tests/smoke_test.py

    WEBSITE_URL=https://example.cloudfront.net \
        python -m pytest tests/smoke_test.py

Optional environment variables:
    WEBSITE_URL:
        HTTPS website endpoint. Defaults to https://localhost, which should
        be overridden for a real deployment.

    REQUEST_TIMEOUT:
        HTTP request timeout in seconds. Defaults to 15.

    MAX_REDIRECTS:
        Maximum number of redirects to follow. Defaults to 5.

    EXPECTED_TITLE:
        Optional expected HTML title text.

    VERIFY_ASSETS:
        Whether to verify referenced CSS and JavaScript assets.
        Defaults to true.

    VERIFY_SECURITY_HEADERS:
        Whether to verify expected security response headers.
        Defaults to true.

    ALLOW_HTTP:
        Set to true only for an intentional local HTTP test endpoint.
        Defaults to false.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import pytest
import requests


DEFAULT_WEBSITE_URL = "https://localhost"
DEFAULT_REQUEST_TIMEOUT = 15
DEFAULT_MAX_REDIRECTS = 5

HTML_CONTENT_TYPE = "text/html"
CSS_CONTENT_TYPE = "text/css"
JAVASCRIPT_CONTENT_TYPES = (
    "application/javascript",
    "text/javascript",
)

SECURITY_HEADERS = {
    "strict-transport-security": (
        "Strict-Transport-Security",
    ),
    "content-security-policy": (
        "Content-Security-Policy",
    ),
    "x-content-type-options": (
        "X-Content-Type-Options",
    ),
    "x-frame-options": (
        "X-Frame-Options",
    ),
    "referrer-policy": (
        "Referrer-Policy",
    ),
}


@dataclass(frozen=True)
class SmokeTestConfig:
    """Runtime configuration for website smoke tests."""

    website_url: str
    request_timeout: int
    max_redirects: int
    expected_title: str | None
    verify_assets: bool
    verify_security_headers: bool
    allow_http: bool

    @classmethod
    def from_environment(cls) -> SmokeTestConfig:
        """Build configuration from environment variables."""
        website_url = os.getenv(
            "WEBSITE_URL",
            DEFAULT_WEBSITE_URL,
        ).strip()

        request_timeout = int(
            os.getenv(
                "REQUEST_TIMEOUT",
                str(DEFAULT_REQUEST_TIMEOUT),
            )
        )

        max_redirects = int(
            os.getenv(
                "MAX_REDIRECTS",
                str(DEFAULT_MAX_REDIRECTS),
            )
        )

        expected_title = os.getenv(
            "EXPECTED_TITLE",
        )

        verify_assets = parse_boolean_environment_variable(
            "VERIFY_ASSETS",
            default=True,
        )

        verify_security_headers = parse_boolean_environment_variable(
            "VERIFY_SECURITY_HEADERS",
            default=True,
        )

        allow_http = parse_boolean_environment_variable(
            "ALLOW_HTTP",
            default=False,
        )

        return cls(
            website_url=website_url.rstrip("/"),
            request_timeout=request_timeout,
            max_redirects=max_redirects,
            expected_title=expected_title,
            verify_assets=verify_assets,
            verify_security_headers=verify_security_headers,
            allow_http=allow_http,
        )


def parse_boolean_environment_variable(
    name: str,
    default: bool,
) -> bool:
    """Parse a boolean environment variable safely."""
    value = os.getenv(name)

    if value is None:
        return default

    normalized_value = value.strip().lower()

    if normalized_value in {"true", "1", "yes", "on"}:
        return True

    if normalized_value in {"false", "0", "no", "off"}:
        return False

    raise ValueError(
        f"{name} must be one of true, false, 1, 0, yes, no, on, or off."
    )


@pytest.fixture(scope="session")
def config() -> SmokeTestConfig:
    """Provide shared smoke-test configuration."""
    configuration = SmokeTestConfig.from_environment()

    if configuration.request_timeout <= 0:
        raise ValueError("REQUEST_TIMEOUT must be greater than zero.")

    if configuration.max_redirects < 0:
        raise ValueError("MAX_REDIRECTS cannot be negative.")

    parsed_url = urlparse(configuration.website_url)

    if parsed_url.scheme not in {"http", "https"}:
        raise ValueError(
            "WEBSITE_URL must use either HTTPS or HTTP."
        )

    if not parsed_url.netloc:
        raise ValueError(
            "WEBSITE_URL must contain a valid hostname."
        )

    if parsed_url.username or parsed_url.password:
        raise ValueError(
            "WEBSITE_URL must not contain embedded credentials."
        )

    if parsed_url.scheme != "https" and not configuration.allow_http:
        raise ValueError(
            "WEBSITE_URL must use HTTPS. Set ALLOW_HTTP=true only "
            "for intentional local HTTP testing."
        )

    return configuration


@pytest.fixture(scope="session")
def http_session() -> requests.Session:
    """Provide a reusable HTTP session."""
    session = requests.Session()

    session.headers.update(
        {
            "User-Agent": "S3-Static-Website-Smoke-Test/1.0",
            "Accept": "text/html,application/xhtml+xml",
        }
    )

    yield session

    session.close()


def request_website(
    session: requests.Session,
    url: str,
    config: SmokeTestConfig,
) -> requests.Response:
    """Perform a bounded GET request against the website."""
    try:
        response = session.get(
            url,
            timeout=config.request_timeout,
            allow_redirects=True,
        )
    except requests.Timeout as exc:
        pytest.fail(
            f"Request timed out after {config.request_timeout} seconds: "
            f"{url}. Error: {exc}"
        )
    except requests.ConnectionError as exc:
        pytest.fail(
            f"Could not connect to website endpoint {url}. "
            f"Check DNS, CloudFront distribution status, and origin "
            f"availability. Error: {exc}"
        )
    except requests.RequestException as exc:
        pytest.fail(
            f"Website request failed for {url}. Error: {exc}"
        )

    if len(response.history) > config.max_redirects:
        pytest.fail(
            f"Website exceeded the configured redirect limit of "
            f"{config.max_redirects}. Observed redirects: "
            f"{len(response.history)}."
        )

    return response


def assert_successful_response(
    response: requests.Response,
    requested_url: str,
) -> None:
    """Validate that an endpoint returns a successful response."""
    assert response.status_code == requests.codes.ok, (
        f"Expected HTTP 200 for {requested_url}, "
        f"received HTTP {response.status_code}. "
        f"Final URL: {response.url}. "
        f"Response excerpt: {response.text[:500]}"
    )


def normalize_content_type(response: requests.Response) -> str:
    """Return the normalized media type without charset parameters."""
    return (
        response.headers.get("Content-Type", "")
        .split(";", maxsplit=1)[0]
        .strip()
        .lower()
    )


def extract_html_assets(
    html_content: str,
    base_url: str,
) -> list[tuple[str, str]]:
    """Extract local stylesheet and JavaScript references."""
    assets = []

    stylesheet_pattern = re.compile(
        r'<link\b[^>]*\bhref\s*=\s*["\']([^"\']+)["\']'
        r'[^>]*>',
        re.IGNORECASE,
    )

    script_pattern = re.compile(
        r'<script\b[^>]*\bsrc\s*=\s*["\']([^"\']+)["\']'
        r'[^>]*>',
        re.IGNORECASE,
    )

    for match in stylesheet_pattern.finditer(html_content):
        tag = match.group(0)

        if not re.search(
            r'\brel\s*=\s*["\']stylesheet["\']',
            tag,
            re.IGNORECASE,
        ):
            continue

        asset_url = urljoin(
            base_url,
            match.group(1),
        )

        assets.append(
            ("stylesheet", asset_url)
        )

    for match in script_pattern.finditer(html_content):
        asset_url = urljoin(
            base_url,
            match.group(1),
        )

        assets.append(
            ("javascript", asset_url)
        )

    return assets


def assert_asset_response(
    response: requests.Response,
    asset_type: str,
    asset_url: str,
) -> None:
    """Validate an individual static asset response."""
    assert_successful_response(
        response,
        asset_url,
    )

    content_type = normalize_content_type(response)

    if asset_type == "stylesheet":
        assert content_type == CSS_CONTENT_TYPE, (
            f"Expected CSS content type for {asset_url}, "
            f"received {content_type!r}."
        )

    elif asset_type == "javascript":
        assert content_type in JAVASCRIPT_CONTENT_TYPES, (
            f"Expected JavaScript content type for {asset_url}, "
            f"received {content_type!r}."
        )

    assert len(response.content) > 0, (
        f"Asset response is empty: {asset_url}"
    )


def test_website_endpoint_is_reachable(
    config: SmokeTestConfig,
    http_session: requests.Session,
) -> None:
    """Verify that the website endpoint is reachable over HTTP."""
    response = request_website(
        session=http_session,
        url=config.website_url,
        config=config,
    )

    assert_successful_response(
        response,
        config.website_url,
    )

    assert response.url.startswith("https://") or config.allow_http, (
        f"Website redirected to a non-HTTPS endpoint: {response.url}"
    )


def test_website_returns_html(
    config: SmokeTestConfig,
    http_session: requests.Session,
) -> None:
    """Verify that the root endpoint serves HTML."""
    response = request_website(
        session=http_session,
        url=config.website_url,
        config=config,
    )

    assert_successful_response(
        response,
        config.website_url,
    )

    content_type = normalize_content_type(response)

    assert content_type == HTML_CONTENT_TYPE, (
        f"Expected {HTML_CONTENT_TYPE}, received {content_type!r}."
    )

    assert response.content, (
        "Website returned an empty HTML response."
    )

    assert re.search(
        r"<html\b",
        response.text,
        re.IGNORECASE,
    ), "Website response does not contain an HTML document."


def test_expected_page_title(
    config: SmokeTestConfig,
    http_session: requests.Session,
) -> None:
    """Verify the configured page title when one is provided."""
    if not config.expected_title:
        pytest.skip(
            "EXPECTED_TITLE is not configured."
        )

    response = request_website(
        session=http_session,
        url=config.website_url,
        config=config,
    )

    assert_successful_response(
        response,
        config.website_url,
    )

    title_match = re.search(
        r"<title\b[^>]*>(.*?)</title>",
        response.text,
        re.IGNORECASE | re.DOTALL,
    )

    assert title_match is not None, (
        "The website HTML does not contain a title element."
    )

    actual_title = re.sub(
        r"\s+",
        " ",
        title_match.group(1),
    ).strip()

    assert config.expected_title.casefold() in actual_title.casefold(), (
        f"Expected title to contain {config.expected_title!r}, "
        f"received {actual_title!r}."
    )


def test_static_assets_are_available(
    config: SmokeTestConfig,
    http_session: requests.Session,
) -> None:
    """Verify that referenced CSS and JavaScript assets are accessible."""
    if not config.verify_assets:
        pytest.skip(
            "Static asset verification is disabled."
        )

    response = request_website(
        session=http_session,
        url=config.website_url,
        config=config,
    )

    assert_successful_response(
        response,
        config.website_url,
    )

    assets = extract_html_assets(
        html_content=response.text,
        base_url=response.url,
    )

    assert assets, (
        "No stylesheet or JavaScript references were found in the "
        "website HTML."
    )

    for asset_type, asset_url in assets:
        parsed_asset_url = urlparse(asset_url)

        if parsed_asset_url.scheme not in {"http", "https"}:
            pytest.fail(
                f"Unsupported asset URL scheme: {asset_url}"
            )

        if parsed_asset_url.netloc != urlparse(response.url).netloc:
            continue

        asset_response = request_website(
            session=http_session,
            url=asset_url,
            config=config,
        )

        assert_asset_response(
            response=asset_response,
            asset_type=asset_type,
            asset_url=asset_url,
        )


def test_security_response_headers(
    config: SmokeTestConfig,
    http_session: requests.Session,
) -> None:
    """Verify expected security headers on the website response."""
    if not config.verify_security_headers:
        pytest.skip(
            "Security header verification is disabled."
        )

    response = request_website(
        session=http_session,
        url=config.website_url,
        config=config,
    )

    assert_successful_response(
        response,
        config.website_url,
    )

    for header_name, _ in SECURITY_HEADERS.items():
        assert header_name in {
            key.lower()
            for key in response.headers
        }, (
            f"Expected security header {header_name!r} was not present. "
            "Check the CloudFront response headers policy."
        )

    assert response.headers.get(
        "X-Content-Type-Options",
        "",
    ).lower() == "nosniff", (
        "X-Content-Type-Options should be set to nosniff."
    )


def test_website_does_not_expose_s3_website_endpoint(
    config: SmokeTestConfig,
    http_session: requests.Session,
) -> None:
    """Verify that the public website URL is not an S3 website endpoint."""
    parsed_url = urlparse(config.website_url)
    hostname = parsed_url.hostname or ""

    s3_website_patterns = (
        r"\.s3-website[.-][a-z0-9-]+\.amazonaws\.com$",
        r"\.s3-website\.amazonaws\.com$",
    )

    assert not any(
        re.search(pattern, hostname, re.IGNORECASE)
        for pattern in s3_website_patterns
    ), (
        "The configured public endpoint appears to be an S3 website "
        "endpoint. This project expects a private S3 origin delivered "
        "through CloudFront."
    )