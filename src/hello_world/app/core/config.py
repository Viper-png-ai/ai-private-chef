from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv



PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(PROJECT_ROOT / ".env")

def _as_bool(value:str|None,default:bool=False)->bool:
    if value is None:
        return default
    return value.strip().lower() in {"1","true","yes","on"}


@dataclass(frozen=True)
class Settings:
    dashscope_api_key: str
    dashscope_base_url: str
    tavily_api_key: str
    oss_region: str
    oss_endpoint: str
    oss_bucket: str
    oss_access_key_id: str
    oss_access_key_secret: str
    oss_public_base_url: str
    sqlite_path: Path
    jwt_secret: str
    jwt_expire_minutes: int
    cookie_secure: bool
    
       
    @property
    def oss_configured(self) -> bool:
        return all(
            [
                self.oss_region,
                self.oss_endpoint,
                self.oss_bucket,
                self.oss_access_key_id,
                self.oss_access_key_secret,
            ]
        )


sqlite_path = (
    Path(__file__).resolve().parents[1]
    / "db"
    / "personal_chief.db"
)
sqlite_path.parent.mkdir(parents=True, exist_ok=True)

settings = Settings(
    dashscope_api_key=os.getenv("DASHSCOPE_API_KEY", "").strip(),
    dashscope_base_url=os.getenv(
        "DASHSCOPE_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    ).strip(),
    tavily_api_key=os.getenv("TAVILY_API_KEY", "").strip(),
    oss_region=os.getenv("OSS_REGION", "").strip(),
    oss_endpoint=os.getenv("OSS_ENDPOINT", "").strip(),
    oss_bucket=os.getenv("OSS_BUCKET", "").strip(),
    oss_access_key_id=os.getenv("OSS_ACCESS_KEY_ID", "").strip(),
    oss_access_key_secret=os.getenv("OSS_ACCESS_KEY_SECRET", "").strip(),
    oss_public_base_url=os.getenv("OSS_PUBLIC_BASE_URL", "").strip(),
    sqlite_path=sqlite_path,
    jwt_secret=os.getenv(
        "JWT_SECRET",
        "dev-only-change-this-secret",
    ).strip(),
    jwt_expire_minutes=int(
        os.getenv("JWT_EXPIRE_MINUTES", "10080")
    ),
    cookie_secure=_as_bool(
        os.getenv("COOKIE_SECURE"),
        default=False,
    ),
)