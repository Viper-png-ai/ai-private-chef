from fastapi import APIRouter, Depends,HTTPException

from hello_world.app.models.schemas import PresignRequest, PresignResponse
from hello_world.app.services.oss import OSSNotConfiguredError, oss_storage
from hello_world.app.api.dependencies import get_current_user

router = APIRouter(prefix="/oss", tags=["oss"])

@router.post("/presign", response_model=PresignResponse)
def create_presigned_upload(
    payload: PresignRequest,
    user: dict[str, str] = Depends(get_current_user),
)-> PresignResponse:
    if not payload.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只允许上传图片文件。")

    try:
        result = oss_storage.create_upload(
            filename=payload.filename,
            content_type=payload.content_type,
            user_id=user["id"],
            session_id=payload.session_id,
        )
        return PresignResponse(**result)
    except OSSNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"生成 OSS 上传签名失败：{exc}",
        ) from exc
