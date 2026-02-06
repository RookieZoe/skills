#!/usr/bin/env python3
"""
CLI entry point for upload-to-s3like.

This module provides the main entry point for the upload-to-s3like CLI command.
"""

import argparse
import json
import os
import sys

from upload_to_s3like.core import upload_file, upload_directory


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Upload files to S3 and S3-compatible object storage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Upload single file
    upload-to-s3like --path ./file.txt --bucket mybucket

    # Upload directory with prefix
    upload-to-s3like --path ./folder --bucket mybucket --prefix uploads/

    # With custom concurrency and retries
    upload-to-s3like --path ./folder --bucket mybucket --concurrency 10 --retries 3

Environment Variables:
    SKILL__S3_ENDPOINT    - S3 endpoint URL (optional, for MinIO, etc.)
    SKILL__S3_ACCESS_KEY  - S3 access key (required)
    SKILL__S3_SECRET_KEY  - S3 secret key (required)
    SKILL__S3_REGION      - S3 region (default: us-east-1)
    SKILL__S3_SECURE      - Use HTTPS (default: true)
    SKILL__S3_BUCKET      - Default bucket name (optional)
        """,
    )

    parser.add_argument(
        "--path",
        required=True,
        help="Path to file or directory to upload",
    )

    parser.add_argument(
        "--bucket",
        default=None,
        help="S3 bucket name (overrides SKILL__S3_BUCKET env var)",
    )

    parser.add_argument(
        "--prefix",
        default=None,
        help="Optional key prefix for uploaded objects",
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=None,
        help="Max concurrency for uploads (uses boto3 default if not set)",
    )

    parser.add_argument(
        "--retries",
        type=int,
        default=None,
        help="Number of retries for failed uploads (uses boto3 default if not set)",
    )

    args = parser.parse_args()

    # Validate path exists
    if not os.path.exists(args.path):
        print(f"Error: Path not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    # Check for symlink to directory
    if os.path.islink(args.path) and os.path.isdir(args.path):
        print(
            f"Error: Symlink to directory not supported: {args.path}", file=sys.stderr
        )
        sys.exit(1)

    try:
        if os.path.isfile(args.path):
            result = upload_file(
                file_path=args.path,
                bucket=args.bucket,
                prefix=args.prefix,
                concurrency=args.concurrency,
                retries=args.retries,
            )
        else:
            result = upload_directory(
                dir_path=args.path,
                bucket=args.bucket,
                prefix=args.prefix,
                concurrency=args.concurrency,
                retries=args.retries,
            )

        # Output JSON result
        print(json.dumps(result, indent=2))
        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
