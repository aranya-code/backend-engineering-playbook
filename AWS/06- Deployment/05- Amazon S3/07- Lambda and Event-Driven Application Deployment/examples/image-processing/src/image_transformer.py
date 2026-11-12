"""Image transformation utilities for the S3 image-processing Lambda.

The module validates and resizes supported raster images using Pillow.
It is deliberately independent of AWS so that image transformations can
be tested locally without an AWS account or mocked S3 clients.

Public interface:

    create_thumbnail(image_bytes: bytes) -> tuple[bytes, str]

The returned MIME type corresponds to the original image format. The
output format is preserved so that the handler can retain the original
object-key extension when writing the transformed image to S3.
"""

from __future__ import annotations

import io
import logging
import os
import warnings
from typing import Final

from PIL import (
    Image,
    ImageFile,
    ImageOps,
    UnidentifiedImageError,
)


logger = logging.getLogger(__name__)

# Do not accept truncated images. A partially decoded image must not be
# written to the output bucket as if it were a valid transformation.
ImageFile.LOAD_TRUNCATED_IMAGES = False

SUPPORTED_FORMATS: Final[dict[str, str]] = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}

DEFAULT_MAX_WIDTH: Final[int] = 1280
DEFAULT_MAX_HEIGHT: Final[int] = 1280
DEFAULT_MAX_IMAGE_PIXELS: Final[int] = 40_000_000
DEFAULT_JPEG_QUALITY: Final[int] = 85
DEFAULT_WEBP_QUALITY: Final[int] = 85


def _positive_integer_from_env(
    name: str,
    default: int,
) -> int:
    """Read a positive integer configuration value from the environment."""

    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"{name} must be a valid integer"
        ) from exc

    if value <= 0:
        raise ValueError(
            f"{name} must be greater than zero"
        )

    return value


def _bounded_quality_from_env(
    name: str,
    default: int,
) -> int:
    """Read an image quality value in the inclusive range 1 to 100."""

    value = _positive_integer_from_env(name, default)

    if value > 100:
        raise ValueError(
            f"{name} must be between 1 and 100"
        )

    return value


def _validate_image_size(
    image: Image.Image,
    max_image_pixels: int,
) -> None:
    """Reject images whose dimensions exceed the configured pixel limit."""

    width, height = image.size

    if width <= 0 or height <= 0:
        raise ValueError("Image dimensions must be greater than zero")

    pixel_count = width * height

    if pixel_count > max_image_pixels:
        raise ValueError(
            "Image exceeds the maximum allowed pixel count: "
            f"{pixel_count} > {max_image_pixels}"
        )


def _decode_image(
    image_bytes: bytes,
    max_image_pixels: int,
) -> tuple[Image.Image, str]:
    """Validate and fully decode an image from its original byte content."""

    if not isinstance(image_bytes, bytes):
        raise TypeError("image_bytes must be bytes")

    if not image_bytes:
        raise ValueError("Image content must not be empty")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter(
                "error",
                Image.DecompressionBombWarning,
            )

            with Image.open(io.BytesIO(image_bytes)) as image:
                image_format = image.format

                if image_format not in SUPPORTED_FORMATS:
                    raise ValueError(
                        "Unsupported image format. Supported formats: "
                        f"{', '.join(SUPPORTED_FORMATS)}"
                    )

                if getattr(image, "n_frames", 1) != 1:
                    raise ValueError(
                        "Animated and multi-frame images are not supported"
                    )

                _validate_image_size(
                    image,
                    max_image_pixels,
                )

                # Verify the file structure before performing a full decode.
                image.verify()

            # verify() invalidates the image object. Reopen the original
            # bytes to decode the actual pixel data.
            with Image.open(io.BytesIO(image_bytes)) as image:
                if image.format != image_format:
                    raise ValueError(
                        "Image format changed during validation"
                    )

                _validate_image_size(
                    image,
                    max_image_pixels,
                )

                image.load()

                # Apply EXIF orientation before calculating the thumbnail.
                # This prevents portrait images from being resized using
                # their unrotated dimensions.
                normalized_image = ImageOps.exif_transpose(image)

                # Detach the decoded image from the BytesIO source and the
                # Pillow context manager before returning it.
                normalized_image = normalized_image.copy()

    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise ValueError(
            "Image dimensions exceed Pillow's decompression safety limit"
        ) from exc
    except UnidentifiedImageError as exc:
        raise ValueError(
            "Input does not contain a recognizable image"
        ) from exc
    except OSError as exc:
        raise ValueError(
            "Image is corrupted or could not be decoded"
        ) from exc

    return normalized_image, image_format


def _prepare_jpeg(image: Image.Image) -> Image.Image:
    """Convert an image to JPEG-compatible RGB pixels.

    Transparent images are composited onto a white background rather than
    allowing an implicit conversion to discard transparency unpredictably.
    """

    if image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    ):
        rgba_image = image.convert("RGBA")

        background = Image.new(
            "RGB",
            rgba_image.size,
            (255, 255, 255),
        )

        alpha_channel = rgba_image.getchannel("A")

        background.paste(
            rgba_image,
            mask=alpha_channel,
        )

        return background

    if image.mode != "RGB":
        return image.convert("RGB")

    return image


def _prepare_png_or_webp(
    image: Image.Image,
) -> Image.Image:
    """Normalize PNG and WebP modes while preserving transparency."""

    if image.mode in ("RGBA", "LA"):
        return image.convert("RGBA")

    if image.mode == "P":
        if "transparency" in image.info:
            return image.convert("RGBA")

        return image.convert("RGB")

    if image.mode == "1":
        return image.convert("L")

    if image.mode not in ("RGB", "RGBA", "L", "LA"):
        return image.convert("RGB")

    return image


def _encode_image(
    image: Image.Image,
    image_format: str,
    jpeg_quality: int,
    webp_quality: int,
    icc_profile: bytes | None,
) -> bytes:
    """Encode a resized image using its original supported format."""

    output = io.BytesIO()

    save_options: dict[str, object] = {}

    if image_format == "JPEG":
        image = _prepare_jpeg(image)

        save_options.update(
            {
                "quality": jpeg_quality,
                "optimize": True,
                "progressive": True,
            }
        )

    elif image_format == "PNG":
        image = _prepare_png_or_webp(image)

        save_options.update(
            {
                "optimize": True,
                "compress_level": 9,
            }
        )

    elif image_format == "WEBP":
        image = _prepare_png_or_webp(image)

        save_options.update(
            {
                "quality": webp_quality,
                "method": 6,
            }
        )

    else:
        raise ValueError(
            f"Unsupported output image format: {image_format}"
        )

    # Preserve a valid embedded color profile, but intentionally do not
    # copy EXIF metadata or other source metadata into the transformed file.
    if icc_profile:
        save_options["icc_profile"] = icc_profile

    try:
        image.save(
            output,
            format=image_format,
            **save_options,
        )
    except OSError as exc:
        raise ValueError(
            f"Unable to encode transformed {image_format} image"
        ) from exc

    encoded_bytes = output.getvalue()

    if not encoded_bytes:
        raise ValueError("Image encoder returned empty output")

    return encoded_bytes


def create_thumbnail(
    image_bytes: bytes,
) -> tuple[bytes, str]:
    """Create a bounded thumbnail while preserving the source format.

    The image is resized proportionally. Neither dimension exceeds the
    configured maximum, and smaller images are not enlarged.

    Configuration:

        THUMBNAIL_MAX_WIDTH
            Maximum output width in pixels. Defaults to 1280.

        THUMBNAIL_MAX_HEIGHT
            Maximum output height in pixels. Defaults to 1280.

        MAX_IMAGE_PIXELS
            Maximum decoded input pixel count. Defaults to 40,000,000.

        JPEG_QUALITY
            JPEG output quality from 1 to 100. Defaults to 85.

        WEBP_QUALITY
            WebP output quality from 1 to 100. Defaults to 85.

    Supported formats:

        JPEG
        PNG
        WebP

    Animated and multi-frame images are rejected. The function does not
    perform network or AWS operations and raises ValueError for invalid,
    unsupported, corrupted, or oversized image content.

    Returns:
        A tuple containing the transformed image bytes and MIME type.

    Raises:
        TypeError: If image_bytes is not bytes.
        ValueError: If configuration or image content is invalid.
    """

    max_width = _positive_integer_from_env(
        "THUMBNAIL_MAX_WIDTH",
        DEFAULT_MAX_WIDTH,
    )
    max_height = _positive_integer_from_env(
        "THUMBNAIL_MAX_HEIGHT",
        DEFAULT_MAX_HEIGHT,
    )
    max_image_pixels = _positive_integer_from_env(
        "MAX_IMAGE_PIXELS",
        DEFAULT_MAX_IMAGE_PIXELS,
    )
    jpeg_quality = _bounded_quality_from_env(
        "JPEG_QUALITY",
        DEFAULT_JPEG_QUALITY,
    )
    webp_quality = _bounded_quality_from_env(
        "WEBP_QUALITY",
        DEFAULT_WEBP_QUALITY,
    )

    image, image_format = _decode_image(
        image_bytes,
        max_image_pixels,
    )

    try:
        original_width, original_height = image.size
        icc_profile = image.info.get("icc_profile")

        image.thumbnail(
            (max_width, max_height),
            Image.Resampling.LANCZOS,
            reducing_gap=3.0,
        )

        if image.width <= 0 or image.height <= 0:
            raise ValueError(
                "Resizing produced invalid image dimensions"
            )

        thumbnail_bytes = _encode_image(
            image=image,
            image_format=image_format,
            jpeg_quality=jpeg_quality,
            webp_quality=webp_quality,
            icc_profile=icc_profile,
        )

        mime_type = SUPPORTED_FORMATS[image_format]

        logger.info(
            "Image transformation completed: "
            "format=%s original_width=%d original_height=%d "
            "output_width=%d output_height=%d "
            "input_size_bytes=%d output_size_bytes=%d",
            image_format,
            original_width,
            original_height,
            image.width,
            image.height,
            len(image_bytes),
            len(thumbnail_bytes),
        )

        return thumbnail_bytes, mime_type

    finally:
        image.close()