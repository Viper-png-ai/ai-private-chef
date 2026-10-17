from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse,quote
from uuid import uuid4

from alibabacloud_oss_v2 import Client, Config, models
from alibabacloud_oss_v2.credentials import StaticCredentialsProvider

from hello_world.app.core.config import settings

class OSSNotConfiguredError(RuntimeError):
    pass

class OSSStorage:
    def __init__(self) -> None:
        self.client: Client | None = None

        if settings.oss_configured:
            self.client = Client(
                Config(
                    region=settings.oss_region,
                    endpoint=settings.oss_endpoint,
                    credentials_provider=StaticCredentialsProvider(
                        settings.oss_access_key_id,
                        settings.oss_access_key_secret,
                    ),
                )
            )

    def _require_client(self) -> Client:
        if self.client is None:
            raise OSSNotConfiguredError(
                "OSS 配置不完整，请检查 OSS_REGION、OSS_ENDPOINT、"
                "OSS_BUCKET、OSS_ACCESS_KEY_ID 和 OSS_ACCESS_KEY_SECRET。"
            )
        return self.client

    def create_upload(
        self,
        filename: str,
        content_type: str,
        user_id:str,
        session_id: str,
    ) -> dict[str, object]:
        client = self._require_client()
        suffix = Path(filename).suffix.lower()
        object_key = f"ai-chef/{session_id}/{uuid4().hex}{suffix}"

        request = models.PutObjectRequest(
            bucket=settings.oss_bucket,
            key=object_key,
            content_type=content_type,
        )

        result = client.presign(
            request,
            expires=timedelta(minutes=15),
        )

        return {
            "method": result.method or "PUT",
            "upload_url": result.url,
            "headers": dict(result.signed_headers or {}),
            "object_key": object_key,
            "public_url": self.public_url(object_key),
            "expires_in": 900,
        }

    def public_url(self, object_key: str) -> str:
        encoded_key = quote(object_key, safe="/")

        if settings.oss_public_base_url:
            return f"{settings.oss_public_base_url.rstrip('/')}/{encoded_key}"

        endpoint = settings.oss_endpoint
        if endpoint.startswith(("http://", "https://")):
            parsed = urlparse(endpoint)
            scheme = parsed.scheme
            host = parsed.netloc
        else:
            scheme = "https"
            host = endpoint

        return f"{scheme}://{settings.oss_bucket}.{host}/{encoded_key}"


oss_storage = OSSStorage()



