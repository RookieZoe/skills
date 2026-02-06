"""Core upload functionality for S3 and S3-compatible object storage."""

import json
import os
import urllib.request
from pathlib import Path
from typing import Optional

import boto3
from botocore.config import Config
from boto3.s3.transfer import TransferConfig


def _get_s3_client(
    endpoint: Optional[str] = None,
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    region: Optional[str] = None,
    use_ssl: bool = True,
    retries: Optional[int] = None,
):
    """Create and return an S3 client."""
    # Get values from env vars if not provided
    endpoint = endpoint or os.environ.get("SKILL__S3_ENDPOINT")
    access_key = access_key or os.environ.get("SKILL__S3_ACCESS_KEY")
    secret_key = secret_key or os.environ.get("SKILL__S3_SECRET_KEY")
    region = region or os.environ.get("SKILL__S3_REGION", "us-east-1")
    use_ssl_str = os.environ.get("SKILL__S3_SECURE", "true").lower()
    use_ssl = use_ssl if use_ssl is not None else (use_ssl_str == "true")

    if not access_key or not secret_key:
        raise ValueError("SKILL__S3_ACCESS_KEY and SKILL__S3_SECRET_KEY must be set")

    # Build client config
    config_kwargs = {"region_name": region}
    if retries is not None:
        config_kwargs["retries"] = {"max_attempts": retries, "mode": "adaptive"}

    client_kwargs = {
        "service_name": "s3",
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
        "config": Config(**config_kwargs),
    }

    if endpoint:
        if not endpoint.startswith("http://") and not endpoint.startswith("https://"):
            use_ssl_env = os.environ.get("SKILL__S3_SECURE", "true").lower()
            scheme = "https" if use_ssl_env == "true" else "http"
            endpoint = f"{scheme}://{endpoint}"
        client_kwargs["endpoint_url"] = endpoint

    return boto3.client(**client_kwargs)


def _build_url(
    bucket: str, key: str, endpoint: Optional[str] = None, region: Optional[str] = None
) -> Optional[str]:
    """Build and return an accessible URL for the object, or None if not accessible."""
    urls_to_try = []

    if endpoint:
        # Path-style URL for custom endpoints
        scheme = "https"
        if endpoint.startswith("http://"):
            scheme = "http"
            endpoint = endpoint[7:]
        elif endpoint.startswith("https://"):
            endpoint = endpoint[8:]
        urls_to_try.append(f"{scheme}://{endpoint}/{bucket}/{key}")
    else:
        # AWS S3 style URLs
        if region and region != "us-east-1":
            urls_to_try.append(f"https://{bucket}.s3.{region}.amazonaws.com/{key}")
        urls_to_try.append(f"https://{bucket}.s3.amazonaws.com/{key}")

    # Try HEAD request to verify accessibility
    for url in urls_to_try:
        try:
            req = urllib.request.Request(url, method="HEAD")
            req.add_header("User-Agent", "upload-to-s3like/0.1.0")
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    return url
        except Exception:
            continue

    return None


def upload_file(
    file_path: str,
    bucket: Optional[str] = None,
    prefix: Optional[str] = None,
    concurrency: Optional[int] = None,
    retries: Optional[int] = None,
) -> dict:
    """Upload a single file to S3 or S3-compatible storage."""
    # Resolve bucket
    bucket = bucket or os.environ.get("SKILL__S3_BUCKET")
    if not bucket:
        raise ValueError(
            "Bucket must be provided via --bucket or SKILL__S3_BUCKET env var"
        )

    # Resolve file path and get key
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Build object key
    key = path.name
    if prefix:
        # Normalize prefix: remove leading slashes, ensure trailing slash
        prefix = prefix.lstrip("/")
        if not prefix.endswith("/"):
            prefix += "/"
        key = prefix + key

    # Get S3 client
    client = _get_s3_client(retries=retries)

    # Build transfer config
    transfer_config = None
    if concurrency is not None:
        transfer_config = TransferConfig(max_concurrency=concurrency)

    # Upload
    try:
        extra_args = {"ContentType": "application/octet-stream"}
        client.upload_file(
            str(path),
            bucket,
            key,
            ExtraArgs=extra_args,
            Config=transfer_config,
        )
    except Exception as e:
        raise RuntimeError(f"Upload failed: {e}")

    # Build result
    result = {
        "type": "file",
        "bucket": bucket,
        "key": key,
        "status": "success",
    }

    # Try to get accessible URL
    endpoint = os.environ.get("SKILL__S3_ENDPOINT")
    region = os.environ.get("SKILL__S3_REGION", "us-east-1")
    url = _build_url(bucket, key, endpoint=endpoint, region=region)
    if url:
        result["url"] = url

    return result


def upload_directory(
    dir_path: str,
    bucket: Optional[str] = None,
    prefix: Optional[str] = None,
    concurrency: Optional[int] = None,
    retries: Optional[int] = None,
) -> dict:
    """Upload all files in a directory to S3 or S3-compatible storage."""
    # Resolve bucket
    bucket = bucket or os.environ.get("SKILL__S3_BUCKET")
    if not bucket:
        raise ValueError(
            "Bucket must be provided via --bucket or SKILL__S3_BUCKET env var"
        )

    # Resolve directory path
    root_path = Path(dir_path).resolve()
    if not root_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {dir_path}")

    # Get S3 client
    client = _get_s3_client(retries=retries)

    # Build transfer config
    transfer_config = None
    if concurrency is not None:
        transfer_config = TransferConfig(max_concurrency=concurrency)

    # Prepare prefix
    base_prefix = ""
    if prefix:
        base_prefix = prefix.lstrip("/")
        if not base_prefix.endswith("/"):
            base_prefix += "/"

    # Include root folder name in key
    root_name = root_path.name
    if root_name:
        base_prefix += root_name + "/"

    # Collect files to upload
    files_to_upload = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Filter out hidden directories and symlink directories
        dirnames[:] = [
            d
            for d in dirnames
            if not d.startswith(".") and not os.path.islink(os.path.join(dirpath, d))
        ]

        for filename in filenames:
            # Skip hidden files
            if filename.startswith("."):
                continue

            local_path = Path(dirpath) / filename

            # Handle symlinks to files - resolve and use symlink path as key
            if os.path.islink(local_path):
                target = os.path.realpath(local_path)
                if os.path.isfile(target):
                    local_path = Path(target)
                else:
                    continue  # Skip symlinks to non-files

            # Calculate relative path from root
            rel_path = local_path.relative_to(root_path)
            key = base_prefix + str(rel_path)

            files_to_upload.append(
                {
                    "local_path": str(local_path),
                    "key": key,
                }
            )

    # Upload files
    success_count = 0
    failed_files = []

    for file_info in files_to_upload:
        try:
            extra_args = {"ContentType": "application/octet-stream"}
            client.upload_file(
                file_info["local_path"],
                bucket,
                file_info["key"],
                ExtraArgs=extra_args,
                Config=transfer_config,
            )
            success_count += 1
        except Exception as e:
            failed_files.append(
                {
                    "path": file_info["local_path"],
                    "key": file_info["key"],
                    "error": str(e),
                }
            )

    # Build result
    result = {
        "type": "directory",
        "bucket": bucket,
        "prefix": base_prefix if base_prefix else None,
        "success": success_count,
        "failed": len(failed_files),
    }

    if failed_files:
        result["failed_files"] = failed_files

    return result
