from __future__ import annotations

import os
from typing import BinaryIO, Optional, Union, Dict

# boto3/botocore are the standard, well-supported S3 client libraries and
# work with Backblaze B2's S3-compatible API.
try:
    import boto3
    from botocore.config import Config as BotoConfig
    from botocore.exceptions import BotoCoreError, ClientError
except Exception as e:  # pragma: no cover - import-time failure surfaced clearly at runtime
    boto3 = None  # type: ignore
    BotoConfig = None  # type: ignore
    ClientError = BotoCoreError  # type: ignore


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _get_client_and_bucket():
    """
    Build and return a (s3_client, bucket_name) tuple using environment variables.

    Required env vars:
      - S3_APP_KEY_ID
      - S3_APP_KEY
      - S3_BUCKET
      - S3_ENDPOINT (e.g., s3.us-east-005.backblazeb2.com)

    Optional env vars:
      - S3_APP_KEY_NAME (not needed for S3 API calls but read for completeness)
    """
    if boto3 is None:
        raise RuntimeError(
            "boto3 is not installed. Please add boto3 to your backend dependencies.")

    access_key = _required_env("S3_APP_KEY_ID")
    secret_key = _required_env("S3_APP_KEY")
    bucket = _required_env("S3_BUCKET")
    endpoint = _required_env("S3_ENDPOINT")

    # Optional (not strictly needed for API usage)
    os.getenv("S3_APP_KEY_NAME")

    # Normalize endpoint URL
    endpoint_url = endpoint
    if not endpoint_url.startswith("http://") and not endpoint_url.startswith("https://"):
        endpoint_url = f"https://{endpoint_url}"

    s3_config = BotoConfig(signature_version="s3v4", s3={"addressing_style": "virtual"})

    client = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        endpoint_url=endpoint_url,
        config=s3_config,
    )

    return client, bucket


def _make_key(table_name: str, record_id: Union[int, str]) -> str:
    if not table_name or not str(record_id):
        raise ValueError("table_name and record_id are required")
    # Enforce simple naming convention: [table_name]-[record_id]
    return f"{table_name}-{record_id}"


def create_file(
    table_name: str,
    record_id: Union[int, str],
    data: Union[bytes, BinaryIO],
    *,
    content_type: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
) -> str:
    """
    Create/overwrite a file in the S3 bucket using the naming convention
    [table_name]-[record_id]. Returns the object key.

    - data: either raw bytes or a file-like object opened in binary mode.
    - content_type: optional MIME type to store alongside the object.
    - metadata: optional user metadata dict (string keys/values).
    """
    s3, bucket = _get_client_and_bucket()
    key = _make_key(table_name, record_id)

    extra_args: Dict[str, str] = {}
    if content_type:
        extra_args["ContentType"] = content_type
    if metadata:
        # User metadata keys are sent as-is; values must be strings
        extra_args["Metadata"] = {k: str(v) for k, v in metadata.items()}

    try:
        if isinstance(data, (bytes, bytearray, memoryview)):
            s3.put_object(Bucket=bucket, Key=key, Body=data, **extra_args)
        else:
            # Assume file-like
            s3.upload_fileobj(Fileobj=data, Bucket=bucket, Key=key, ExtraArgs=extra_args or None)
    except (ClientError, BotoCoreError) as e:  # pragma: no cover
        raise RuntimeError(f"Failed to upload object '{key}' to bucket '{bucket}': {e}")

    return key


def delete_file(table_name: str, record_id: Union[int, str]) -> bool:
    """Delete the file for the given table and id. Returns True if delete request succeeded."""
    s3, bucket = _get_client_and_bucket()
    key = _make_key(table_name, record_id)
    try:
        s3.delete_object(Bucket=bucket, Key=key)
        return True
    except (ClientError, BotoCoreError) as e:  # pragma: no cover
        # If Not Found, treat as success (idempotent delete)
        if isinstance(e, ClientError):
            code = e.response.get("Error", {}).get("Code")  # type: ignore[attr-defined]
            if code in {"NoSuchKey", "404"}:
                return True
        raise RuntimeError(f"Failed to delete object '{key}' from bucket '{bucket}': {e}")


def get_download_link(
    table_name: str,
    record_id: Union[int, str],
    file_type: Optional[str] = None,
    *,
    expires_in_seconds: int = 600,
) -> str:
    """
    Generate a pre-signed direct download URL valid for `expires_in_seconds` (default 10 minutes).

    - file_type: optional MIME type (e.g., "image/jpeg", "application/pdf"). If provided, we set
      the response content-type headers so the browser treats the file appropriately.
    """
    if expires_in_seconds <= 0:
        raise ValueError("expires_in_seconds must be positive")

    s3, bucket = _get_client_and_bucket()
    key = _make_key(table_name, record_id)

    params: Dict[str, str] = {"Bucket": bucket, "Key": key}

    # For GetObject, we can customize response headers. If file_type is provided, set it.
    if file_type:
        params.update({
            "ResponseContentType": file_type,
        })

    try:
        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params=params,
            ExpiresIn=expires_in_seconds,
        )
        return url
    except (ClientError, BotoCoreError) as e:  # pragma: no cover
        raise RuntimeError(
            f"Failed to create pre-signed URL for object '{key}' in bucket '{bucket}': {e}"
        )


__all__ = [
    "create_file",
    "delete_file",
    "get_download_link",
]
