---
name: upload-to-s3like
description: "Toolkit for uploading files to S3 and S3-compatible object storage. Supports single files and directories with JSON output."
allowed-tools: [Python]
---

# Upload to S3like Skill

Upload files to S3 and S3-compatible object storage services (MinIO, etc.).
Supports file and directory uploads with JSON output.

## Quick Start

1. Install dependencies:

```bash
cd /path/to/upload-to-s3like
uv sync
```

2. Set environment variables (see Env Vars section below)

3. Upload a file:

```bash
/path/to/upload-to-s3like/.venv/bin/python /path/to/upload-to-s3like/scripts/upload.py --path ./file.txt --bucket mybucket
```

## CLI Usage

```bash
# Single file upload
/path/to/upload-to-s3like/.venv/bin/python /path/to/upload-to-s3like/scripts/upload.py --path ./file.txt --bucket mybucket

# Directory upload with prefix
/path/to/upload-to-s3like/.venv/bin/python /path/to/upload-to-s3like/scripts/upload.py --path ./folder --bucket mybucket --prefix uploads/

# With custom concurrency and retries
/path/to/upload-to-s3like/.venv/bin/python /path/to/upload-to-s3like/scripts/upload.py --path ./folder --bucket mybucket --concurrency 10 --retries 3
```

## Module Usage

```python
from upload_to_s3like.core import upload_file, upload_directory

# Upload single file
result = upload_file("./file.txt", bucket="mybucket")
print(result)  # JSON with bucket, key, url (if accessible)

# Upload directory
result = upload_directory("./folder", bucket="mybucket", prefix="uploads/")
print(result)  # JSON with success count, failed count, failed_files list
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SKILL__S3_ENDPOINT` | No | S3 endpoint URL (e.g., http://localhost:9000 for MinIO). If not set, uses AWS S3. |
| `SKILL__S3_ACCESS_KEY` | Yes | S3 access key |
| `SKILL__S3_SECRET_KEY` | Yes | S3 secret key |
| `SKILL__S3_REGION` | No | S3 region (default: us-east-1) |
| `SKILL__S3_SECURE` | No | Use HTTPS (true/false, default: true) |
| `SKILL__S3_BUCKET` | No | Default bucket name (can be overridden with --bucket) |

## Output JSON Schema

### Single File Upload

```json
{
  "type": "file",
  "bucket": "mybucket",
  "key": "path/to/file.txt",
  "url": "https://mybucket.s3.amazonaws.com/path/to/file.txt",
  "status": "success"
}
```

If URL is not accessible, the `url` field is omitted:

```json
{
  "type": "file",
  "bucket": "mybucket",
  "key": "path/to/file.txt",
  "status": "success"
}
```

### Directory Upload

```json
{
  "type": "directory",
  "bucket": "mybucket",
  "prefix": "uploads/",
  "success": 5,
  "failed": 1,
  "failed_files": [
    {
      "path": "/path/to/local/file.txt",
      "key": "uploads/file.txt",
      "error": "Permission denied"
    }
  ]
}
```

## Behavior Notes

- **Hidden files**: Files and directories starting with `.` are skipped
- **Symlinks**: Symlinked files are followed and their target content is uploaded (key uses symlink path). Symlinked directories are skipped.
- **Exit codes**: Exit code 0 for successful or partially successful uploads (with failed_files listed). Exit code 1 for fatal errors (missing env vars, path not found, etc.)
- **URL construction**: The tool attempts to construct accessible URLs. If the URL is not accessible (verified via HEAD request), only bucket and key are returned.
