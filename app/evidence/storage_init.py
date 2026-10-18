"""Create the originals bucket with Object Lock (one-shot `storage-init` service, D85).

Run with the S3 admin identity, never the app identity:

    python -m app.evidence.storage_init

It is safe to run again. It creates the bucket with Object Lock enabled if it is missing,
turns on versioning, sets a default COMPLIANCE retention and then reads the settings back.
If the bucket exists without Object Lock it stops with an error: Object Lock cannot be
added to an existing bucket on every S3 service, and silently using an unlocked bucket
would break FR-03.
"""

from __future__ import annotations

import logging
import os
import re
import sys

from .storage import LOCK_MODE

log = logging.getLogger("pramaan.storage_init")
BUCKET_RE = re.compile(r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")


class InitError(RuntimeError):
    pass


def _env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if not value:
        raise InitError(f"{name} is not set")
    if "change-me" in value:
        raise InitError(f"{name} still contains 'change-me'; run tools/setup_env.py")
    return value


def make_client():  # type: ignore[no-untyped-def]
    import boto3
    from botocore.config import Config

    return boto3.client(
        "s3", endpoint_url=_env("PRAMAAN_S3_ENDPOINT"), region_name="us-east-1",
        aws_access_key_id=_env("PRAMAAN_S3_ADMIN_ACCESS_KEY"),
        aws_secret_access_key=_env("PRAMAAN_S3_ADMIN_SECRET_KEY"),
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}, connect_timeout=5,
                      retries={"max_attempts": 5, "mode": "standard"},
                      request_checksum_calculation="when_required",
                      response_checksum_validation="when_required"),
    )


def ensure_bucket(s3, bucket: str, retention_days: int) -> None:  # type: ignore[no-untyped-def]
    from botocore.exceptions import ClientError

    if not BUCKET_RE.match(bucket):
        raise InitError("bucket name is not valid")
    try:
        s3.head_bucket(Bucket=bucket)
        created = False
    except ClientError as e:
        if str(e.response.get("Error", {}).get("Code")) not in ("404", "NoSuchBucket", "NotFound"):
            raise
        s3.create_bucket(Bucket=bucket, ObjectLockEnabledForBucket=True)
        created = True

    s3.put_bucket_versioning(Bucket=bucket, VersioningConfiguration={"Status": "Enabled"})
    try:
        current = s3.get_object_lock_configuration(Bucket=bucket)["ObjectLockConfiguration"]
    except ClientError as e:
        raise InitError(f"bucket {bucket} has no Object Lock; delete it and run again "
                        "(an empty bucket only)") from e
    if current.get("ObjectLockEnabled") != "Enabled":
        raise InitError(f"bucket {bucket} has no Object Lock")
    s3.put_object_lock_configuration(Bucket=bucket, ObjectLockConfiguration={
        "ObjectLockEnabled": "Enabled",
        "Rule": {"DefaultRetention": {"Mode": LOCK_MODE, "Days": retention_days}},
    })

    # Read back: what the service reports is what counts.
    versioning = s3.get_bucket_versioning(Bucket=bucket).get("Status")
    lock = s3.get_object_lock_configuration(Bucket=bucket)["ObjectLockConfiguration"]
    rule = lock.get("Rule", {}).get("DefaultRetention", {})
    if versioning != "Enabled" or lock.get("ObjectLockEnabled") != "Enabled" or rule.get("Mode") != LOCK_MODE:
        raise InitError("bucket settings did not stick: versioning or Object Lock is not as requested")
    log.info("bucket ready", extra={"bucket": bucket, "bucket_created": created, "mode": LOCK_MODE,
                                    "days": rule.get("Days")})


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    try:
        bucket = _env("PRAMAAN_S3_BUCKET", "pramaan-originals")
        days = int(_env("PRAMAAN_RETENTION_DAYS", "3650"))
        if not 1 <= days <= 36500:
            raise InitError("PRAMAAN_RETENTION_DAYS must be between 1 and 36500")
        ensure_bucket(make_client(), bucket, days)
    except (InitError, ValueError) as e:
        print(f"storage-init: {e}", file=sys.stderr)
        return 1
    print(f"storage-init: bucket {bucket} ready (versioning on, Object Lock {LOCK_MODE}, {days} days)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
