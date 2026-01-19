import asyncio
import json
from typing import Optional

from knwl.di import defaults
from knwl.models import KnwlBlob
from knwl.storage.blob_storage_base import BlobStorageBase


@defaults("blob", "s3")
class S3Storage(BlobStorageBase):
    """
    S3-compatible implementation of `BlobStorageBase`.

    This implementation uses `boto3` (if available) in a blocking fashion wrapped
    with `asyncio.to_thread` so it can be used from async code without adding an
    explicit async dependency.

    Configuration (via DI defaults or constructor):
      - bucket_name: the S3 bucket to use (required)
      - region_name: optional AWS region
      - aws_access_key_id / aws_secret_access_key: optional credentials
      - endpoint_url: optional endpoint (for S3-compatible services)

    Notes:
    - Requires `boto3` to be installed. Use `uv sync --group s3` to add the dependency.
    - You can use SeaweedFS (https://seaweedfs.com/) as a free S3-compatible storage backend
      for local testing and development: `docker run -d --name seaweed -p 8333:8333 -e AWS_ACCESS_KEY_ID=does-not-matter -e AWS_SECRET_ACCESS_KEY=does-not-matter chrislusf/seaweedfs server -s3`
    - The seaweed config can be used with `storage: S3Storage = services.get_service("blob", "seaweed")` in tests or application code.
    """

    def __init__(
        self,
        bucket_name: Optional[str] = "knwl-blobs",
        region_name: Optional[str] = "us-east-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        client=None,
    ) -> None:
        super().__init__()

        # Lazy import so package isn't required at module import time
        try:
            import boto3  # type: ignore
        except Exception as exc:  # pragma: no cover - environment dependent
            boto3 = None  # type: ignore

        self._boto3 = boto3
        self.bucket_name = bucket_name
        self.region_name = region_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.endpoint_url = endpoint_url
        self._client = client

    def _get_client(self):
        if self._client is not None:
            return self._client
        if self._boto3 is None:
            raise RuntimeError("boto3 is required for S3Storage but is not installed.")

        session = self._boto3.session.Session()

        # If explicit credentials were provided, pass them through. When no credentials
        # are available but an endpoint_url is provided (common for local S3-compatible
        # services like SeaweedFS), create an unsigned client to avoid NoCredentialsError.
        client_kwargs = {
            "region_name": self.region_name,
            "endpoint_url": self.endpoint_url,
        }

        if self.aws_access_key_id is not None or self.aws_secret_access_key is not None:
            client_kwargs["aws_access_key_id"] = self.aws_access_key_id
            client_kwargs["aws_secret_access_key"] = self.aws_secret_access_key

        # Prefer an unsigned client when no credentials are set and an endpoint_url exists
        if (
            self.aws_access_key_id is None and self.aws_secret_access_key is None
        ) and self.endpoint_url:
            try:
                from botocore.config import Config  # type: ignore
                from botocore import UNSIGNED  # type: ignore

                client_kwargs["config"] = Config(signature_version=UNSIGNED)
            except Exception:
                # If botocore isn't available for unsigned configuration, fall back to
                # creating a normal client which will raise a clearer error later.
                pass

        client = session.client("s3", **client_kwargs)
        self._client = client
        return client

    async def upsert(self, blob: KnwlBlob) -> str | None:
        self.validate_blob(blob)
        client = self._get_client()

        # Prepare metadata as strings; S3 requires string values for metadata
        metadata = blob.metadata or {}
        meta_headers = {
            "name": blob.name or "",
            "description": blob.description or "",
            "timestamp": str(blob.timestamp) if blob.timestamp is not None else "",
            "type_name": blob.type_name or "",
            "knwl_metadata": json.dumps(metadata, ensure_ascii=False),
        }

        def _put():
            return client.put_object(
                Bucket=self.bucket_name,
                Key=blob.id,
                Body=blob.data,
                Metadata=meta_headers,
            )

        await asyncio.to_thread(_put)
        return blob.id

    async def get_by_id(self, id: str) -> KnwlBlob | None:
        client = self._get_client()

        def _head():
            return client.head_object(Bucket=self.bucket_name, Key=id)

        try:
            head = await asyncio.to_thread(_head)
        except Exception:
            # Treat any failure to head as "not found" to match base contract
            return None

        def _get():
            return client.get_object(Bucket=self.bucket_name, Key=id)

        obj = await asyncio.to_thread(_get)
        body = obj["Body"].read() if obj and obj.get("Body") else b""

        # Parse metadata
        md = head.get("Metadata") or {}
        knwl_meta = {}
        if md.get("knwl_metadata"):
            try:
                knwl_meta = json.loads(md.get("knwl_metadata") or "{}")
            except Exception:
                knwl_meta = {}

        return KnwlBlob(
            id=id,
            name=md.get("name", ""),
            description=md.get("description", ""),
            timestamp=md.get("timestamp"),
            type_name=md.get("type_name"),
            metadata=knwl_meta,
            data=body,
        )

    async def delete_by_id(self, id: str) -> bool:
        client = self._get_client()

        # Check existence first
        def _head():
            return client.head_object(Bucket=self.bucket_name, Key=id)

        try:
            await asyncio.to_thread(_head)
        except Exception:
            return False

        def _delete():
            return client.delete_object(Bucket=self.bucket_name, Key=id)

        await asyncio.to_thread(_delete)
        return True

    async def count(self) -> int:
        client = self._get_client()

        # Use pagination to count objects
        def _count():
            total = 0
            kwargs = {"Bucket": self.bucket_name}
            while True:
                resp = client.list_objects_v2(**kwargs)
                total += resp.get("KeyCount", 0)
                if resp.get("IsTruncated"):
                    kwargs["ContinuationToken"] = resp.get("NextContinuationToken")
                else:
                    break
            return total

        return await asyncio.to_thread(_count)

    async def exists(self, id: str) -> bool:
        client = self._get_client()

        def _head():
            return client.head_object(Bucket=self.bucket_name, Key=id)

        try:
            await asyncio.to_thread(_head)
            return True
        except Exception:
            return False

    def validate_blob(self, blob: KnwlBlob) -> None:
        if blob is not None and blob.id and blob.data:
            return
        raise ValueError("Invalid blob provided for storage.")
